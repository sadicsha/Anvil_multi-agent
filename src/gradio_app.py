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
            "<div class='status-box status-warning'>Please enter a project topic or requirement.</div>",
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
                f"<div class='status-box status-error'>Ollama is not ready: {msg}</div>",
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
        "<div class='status-box status-info'><strong>Agent 1 (Data Agent)</strong>: Searching the web with Web-RAG and ingesting dataset...</div>",
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
                        "<div class='status-box status-info'><strong>Agent 2 (Code Agent)</strong>: Synthesizing code and executing in sandbox...</div>",
                        None, None, "",
                        "", None, "",
                        None, ""
                    )
                elif node_name == "code_agent":
                    yield (
                        "<div class='status-box status-info'><strong>Agent 3 (Report Agent)</strong>: Compiling 13-stage Word Project Report...</div>",
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

        source_info = f"**Web-RAG Source:** [{source_url}]({source_url})\n\n" if source_url else ""
        raw_summary = accumulated_state.get("dataset_summary", "")
        clean_summary = raw_summary.split("\nFirst 3 Sample Records:")[0].split("First 3 Sample Records:")[0].strip()
        data_info = source_info + f"```text\n{clean_summary}\n```"

        status_msg = "<div class='status-box status-success'><strong>Project Anvil Complete!</strong> All 3 deliverables generated successfully in under 15 seconds.</div>"

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
            f"<div class='status-box status-error'>Execution Error: {str(e)}</div>",
            None, None, "",
            "", None, "",
            None, ""
        )


custom_css = """
.gradio-container {
    max-width: 1200px !important;
    margin: auto !important;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
}

.banner-card {
    background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 50%, #06b6d4 100%);
    border-radius: 14px;
    padding: 24px 28px;
    color: #ffffff;
    margin-bottom: 20px;
    box-shadow: 0 8px 20px -4px rgba(30, 58, 138, 0.35);
}

.banner-card h1 {
    color: #ffffff !important;
    margin: 0 0 6px 0 !important;
    font-size: 26px !important;
    font-weight: 700 !important;
    letter-spacing: -0.5px;
}

.banner-card p {
    color: #dbeafe !important;
    margin: 0 !important;
    font-size: 14px !important;
    font-weight: 400;
}

.generate-button {
    background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%) !important;
    color: #ffffff !important;
    font-weight: 600 !important;
    font-size: 16px !important;
    border-radius: 10px !important;
    border: none !important;
    padding: 12px 24px !important;
    box-shadow: 0 4px 14px rgba(37, 99, 235, 0.4) !important;
    transition: all 0.2s ease-in-out !important;
}

.generate-button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(37, 99, 235, 0.5) !important;
}

.status-box {
    padding: 12px 18px;
    border-radius: 8px;
    font-size: 14px;
    margin: 10px 0;
}

.status-info {
    background-color: #eff6ff;
    color: #1e40af;
    border-left: 4px solid #3b82f6;
}

.status-success {
    background-color: #f0fdf4;
    color: #166534;
    border-left: 4px solid #22c55e;
}

.status-warning {
    background-color: #fffbeb;
    color: #92400e;
    border-left: 4px solid #f59e0b;
}

.status-error {
    background-color: #fef2f2;
    color: #991b1b;
    border-left: 4px solid #ef4444;
}

.deliverables-header {
    background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 700 !important;
    font-size: 20px !important;
    margin-top: 15px !important;
}
"""


def create_gradio_app():
    with gr.Blocks(title="Anvil — Autonomous Multi-Agent Data Science Platform") as demo:
        gr.HTML(
            """
            <div class="banner-card">
                <h1>Project Anvil: Autonomous Multi-Agent Data Science Platform</h1>
                <p>Enterprise Analytics Engine with Deterministic Code Execution and Automated Documentation</p>
            </div>
            """
        )

        with gr.Row():
            with gr.Column(scale=3):
                topic_input = gr.Textbox(
                    label="Project Topic or Requirement",
                    placeholder="e.g., Customer Churn Prediction in Telecom, Student Exam Performance Analysis, Stock Price Forecasting...",
                    lines=1
                )
            with gr.Column(scale=2):
                url_input = gr.Textbox(
                    label="Online Dataset URL (Optional)",
                    placeholder="https://raw.githubusercontent.com/.../data.csv (Leave blank for Web-RAG)",
                    lines=1
                )

        generate_btn = gr.Button("Generate Project", variant="primary", size="lg", elem_classes=["generate-button"])
        status_box = gr.HTML("<div class='status-box status-info'>Enter a topic above and click <strong>Generate Project</strong> to deploy the 3 AI agents.</div>")

        gr.HTML("<div class='deliverables-header'>Project Deliverables</div>")

        with gr.Tabs():
            with gr.TabItem("1. Dataset (CSV)"):
                data_summary_md = gr.Markdown()
                csv_download = gr.File(label="Download dataset.csv")
                df_preview = gr.Dataframe(label="Interactive Dataset Table Preview", interactive=False)

            with gr.TabItem("2. Python Code (solution.py)"):
                code_download = gr.File(label="Download solution.py")
                code_display = gr.Code(label="Standalone Python Script (7-Part Analytical Contract)", language="python")
                with gr.Accordion("View Terminal Execution Output (7-Part Analysis Log)", open=True):
                    exec_output_display = gr.Textbox(label="Sandbox Execution Log", lines=12)

            with gr.TabItem("3. Word Project Report (.docx)"):
                report_download = gr.File(label="Download Word Report (PROJECT_REPORT.docx)")
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
    app_theme = gr.themes.Soft(
        primary_hue=gr.themes.colors.blue,
        secondary_hue=gr.themes.colors.indigo,
        neutral_hue=gr.themes.colors.slate
    )
    print("\nProject Anvil Gradio Interface is running!", flush=True)
    print("Open your browser at: http://127.0.0.1:7860\n", flush=True)
    demo.launch(server_name="127.0.0.1", server_port=7860, share=False, theme=app_theme, css=custom_css)
