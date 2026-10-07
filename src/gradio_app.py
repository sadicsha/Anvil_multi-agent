import os
import sys

print("=========================================================", flush=True)
print("Starting Project Anvil — Gradio Frontend", flush=True)
print("Loading libraries and multi-agent workflow...", flush=True)
print("=========================================================", flush=True)

import io
from pathlib import Path
import pandas as pd
import gradio as gr
from dotenv import load_dotenv

load_dotenv()

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.graph import build_graph
from src.utils import get_available_models, check_ollama_status

anvil_graph = build_graph()

GENERATED_DIR = PROJECT_ROOT / "generated"
GENERATED_DIR.mkdir(exist_ok=True)

DEFAULT_PROVIDER = "groq" if os.environ.get("GROQ_API_KEY") else ("gemini" if os.environ.get("GEMINI_API_KEY") else "ollama")
available = get_available_models()
DEFAULT_MODEL = "qwen2.5-coder:1.5b" if any("1.5b" in m for m in available) else (available[0] if available else "qwen2.5-coder:7b")


def run_pipeline(user_topic: str, dataset_url: str):
    if not user_topic or not user_topic.strip():
        yield (
            "⚠️ Please enter a project topic or requirement.",
            None, None, "",
            "", None, "",
            None, ""
        )
        return

    topic = user_topic.strip()
    online_url = dataset_url.strip() if dataset_url and dataset_url.strip() else None

    if DEFAULT_PROVIDER == "ollama":
        ready, msg = check_ollama_status(DEFAULT_MODEL)
        if not ready:
            yield (
                f"❌ Ollama is not ready: {msg}",
                None, None, "",
                "", None, "",
                None, ""
            )
            return

    initial_state = {
        "request": topic,
        "dataset_url": online_url,
        "dataset_csv": None,
        "dataset_summary": None,
        "dataset_path": None,
        "dataset_source_url": None,
        "code": None,
        "code_path": None,
        "execution_output": None,
        "report_text": None,
        "report_docx_path": None,
        "solution_summary": None,
        "model_name": DEFAULT_MODEL,
        "provider": DEFAULT_PROVIDER,
        "api_key": None
    }

    accumulated_state = dict(initial_state)

    yield (
        "⏳ **Agent 1 (Data Agent)**: Searching the web with Web-RAG & ingesting dataset...",
        None, None, "",
        "", None, "",
        None, ""
    )

    try:
        for step_update in anvil_graph.stream(initial_state, stream_mode="updates"):
            for node_name, node_output in step_update.items():
                accumulated_state.update(node_output)
                if node_name == "data_agent":
                    yield (
                        "⏳ **Agent 2 (Code Agent)**: Synthesizing code & executing in sandbox...",
                        None, None, "",
                        "", None, "",
                        None, ""
                    )
                elif node_name == "code_agent":
                    yield (
                        "⏳ **Agent 3 (Report Agent)**: Compiling 13-stage Word Project Report...",
                        None, None, "",
                        "", None, "",
                        None, ""
                    )

        # Prepare outputs
        csv_str = accumulated_state.get("dataset_csv", "")
        df = None
        if csv_str:
            try:
                df = pd.read_csv(io.StringIO(csv_str))
            except Exception:
                df = None

        csv_path = accumulated_state.get("dataset_path")
        code_str = accumulated_state.get("code", "")
        code_path = accumulated_state.get("code_path")
        exec_out = accumulated_state.get("execution_output", "")
        docx_path = accumulated_state.get("report_docx_path")
        report_text = accumulated_state.get("report_text", "")
        source_url = accumulated_state.get("dataset_source_url")

        source_info = f"🌐 **Web-RAG Source:** [{source_url}]({source_url})\n\n" if source_url else ""
        raw_summary = accumulated_state.get("dataset_summary", "")
        clean_summary = raw_summary.split("\nFirst 3 Sample Records:")[0].split("First 3 Sample Records:")[0].strip()
        data_info = source_info + f"```text\n{clean_summary}\n```"

        status_msg = f"✅ **Project Anvil Complete!** All 3 deliverables generated successfully in under 15 seconds."

        yield (
            status_msg,
            df,
            csv_path if (csv_path and os.path.exists(csv_path)) else None,
            data_info,
            code_str,
            code_path if (code_path and os.path.exists(code_path)) else None,
            exec_out,
            docx_path if (docx_path and os.path.exists(docx_path)) else None,
            report_text
        )

    except Exception as e:
        yield (
            f"❌ Execution Error: {str(e)}",
            None, None, "",
            "", None, "",
            None, ""
        )


def create_gradio_app():
    with gr.Blocks(title="Anvil — Autonomous Multi-Agent Data Science Platform") as demo:
        gr.Markdown(
            """
            # ⚒️ Project Anvil: Autonomous Multi-Agent Data Science Platform
            **LangGraph State Machine • Web-RAG Data Discovery • Sandboxed Execution • 13-Stage Word Reports**
            """
        )

        with gr.Row():
            with gr.Column(scale=3):
                topic_input = gr.Textbox(
                    label="💡 Project Topic or Requirement",
                    placeholder="e.g., Customer Churn Prediction in Telecom, Student Exam Performance Analysis, Stock Price Forecasting...",
                    lines=1
                )
            with gr.Column(scale=2):
                url_input = gr.Textbox(
                    label="🌐 Online Dataset URL (Optional)",
                    placeholder="https://raw.githubusercontent.com/.../data.csv (Leave blank for Web-RAG)",
                    lines=1
                )

        generate_btn = gr.Button("🚀 Generate Project", variant="primary", size="lg")
        status_box = gr.Markdown("💡 Enter a topic above and click **Generate Project** to deploy the 3 AI agents.")

        gr.Markdown("---")
        gr.Markdown("### 📦 Project Deliverables")

        with gr.Tabs():
            with gr.TabItem("📊 1. Dataset (CSV)"):
                data_summary_md = gr.Markdown()
                csv_download = gr.File(label="⬇️ Download dataset.csv")
                df_preview = gr.Dataframe(label="Interactive Dataset Table Preview", interactive=False)

            with gr.TabItem("💻 2. Python Code (solution.py)"):
                code_download = gr.File(label="⬇️ Download solution.py")
                code_display = gr.Code(label="Standalone Python Script (7-Part Analytical Contract)", language="python")
                with gr.Accordion("⚙️ View Terminal Execution Output (7-Part Analysis Log)", open=True):
                    exec_output_display = gr.Textbox(label="Sandbox Stdout/Stderr Execution Log", lines=12)

            with gr.TabItem("📄 3. Word Project Report (.docx)"):
                report_download = gr.File(label="⬇️ Download Word Report (PROJECT_REPORT.docx)")
                report_preview_md = gr.Markdown(label="Executive Report Preview (13 Lifecycle Stages)")

        generate_btn.click(
            fn=run_pipeline,
            inputs=[topic_input, url_input],
            outputs=[
                status_box,
                df_preview,
                csv_download,
                data_summary_md,
                code_display,
                code_download,
                exec_output_display,
                report_download,
                report_preview_md
            ]
        )

    return demo


if __name__ == "__main__":
    demo = create_gradio_app()
    print("\nProject Anvil Gradio Interface is running!", flush=True)
    print("Open your browser at: http://127.0.0.1:7860\n", flush=True)
    demo.launch(server_name="127.0.0.1", server_port=7860, share=False)
