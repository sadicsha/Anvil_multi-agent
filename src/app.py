import os
import sys
from pathlib import Path
import json
import time
from datetime import datetime
import io
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.graph import build_graph
from src.utils import get_available_models, check_ollama_status

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Project Anvil — Multi-Agent Data Science Platform",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom colorful styling
st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
    
    /* Vibrant Gradient Header */
    .banner-container {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 50%, #06b6d4 100%);
        border-radius: 14px;
        padding: 24px 28px;
        color: #ffffff;
        margin-bottom: 24px;
        box-shadow: 0 8px 20px -4px rgba(30, 58, 138, 0.35);
    }
    .banner-title {
        color: #ffffff !important;
        margin: 0 0 6px 0 !important;
        font-size: 26px !important;
        font-weight: 700 !important;
        letter-spacing: -0.5px;
    }
    .banner-subtitle {
        color: #dbeafe !important;
        margin: 0 !important;
        font-size: 14px !important;
        font-weight: 400;
    }

    /* Vibrant Primary Button */
    .stButton>button {
        background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%) !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        border: none !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.35) !important;
        transition: all 0.2s ease-in-out !important;
    }
    .stButton>button:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 18px rgba(37, 99, 235, 0.45) !important;
    }

    /* Download Buttons */
    .stDownloadButton>button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        width: 100% !important;
        border: 1px solid #dbeafe !important;
        background-color: #f8fafc !important;
        color: #1e3a8a !important;
    }
    .stDownloadButton>button:hover {
        background-color: #eff6ff !important;
        border-color: #3b82f6 !important;
    }

    div[data-testid="stExpander"] {
        border-radius: 8px;
        border: 1px solid #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# HISTORY & PERSISTENCE
# ============================================================

GENERATED_DIR = PROJECT_ROOT / "generated"
GENERATED_DIR.mkdir(exist_ok=True)
HISTORY_FILE = GENERATED_DIR / "history.json"


def load_history():
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_history(history_list):
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history_list, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


# ============================================================
# CACHED GRAPH
# ============================================================

@st.cache_resource
def get_anvil_graph():
    return build_graph()


anvil_graph = get_anvil_graph()

# ============================================================
# SESSION STATE INITIALIZATION
# ============================================================

if "history" not in st.session_state:
    st.session_state.history = load_history()

if "result" not in st.session_state:
    if st.session_state.history:
        first_h = st.session_state.history[0]
        st.session_state.result = first_h.get("result", first_h)
    else:
        st.session_state.result = None

if "current_topic" not in st.session_state:
    if st.session_state.history:
        first_h = st.session_state.history[0]
        st.session_state.current_topic = first_h.get("topic") or first_h.get("request", "")
    else:
        st.session_state.current_topic = ""

# Auto-detect best model and provider
DEFAULT_PROVIDER = "groq" if os.environ.get("GROQ_API_KEY") else ("gemini" if os.environ.get("GEMINI_API_KEY") else "ollama")
available = get_available_models()
DEFAULT_MODEL = "qwen2.5-coder:1.5b" if any("1.5b" in m for m in available) else (available[0] if available else "qwen2.5-coder:7b")

# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.header("Project History")

    if st.button("New Project", use_container_width=True):
        st.session_state.result = None
        st.session_state.current_topic = ""
        st.rerun()

    st.divider()

    if not st.session_state.history:
        st.caption("No past projects yet.\nGenerated projects will be saved here automatically.")
    else:
        st.caption(f"Saved Projects ({len(st.session_state.history)}):")
        for idx, item in enumerate(st.session_state.history):
            topic_name = item.get("topic") or item.get("request", "Untitled")
            timestamp = item.get("timestamp", "")
            btn_label = f"{topic_name[:24]}...\n({timestamp})" if len(topic_name) > 24 else f"{topic_name}\n({timestamp})"

            if st.button(btn_label, key=f"hist_btn_{idx}", use_container_width=True):
                st.session_state.result = item.get("result", item)
                st.session_state.current_topic = topic_name
                st.rerun()

        st.divider()
        if st.button("Clear History", use_container_width=True):
            st.session_state.history = []
            st.session_state.result = None
            st.session_state.current_topic = ""
            save_history([])
            st.rerun()


# ============================================================
# MAIN APPLICATION INTERFACE
# ============================================================

# Colorful Header Card
st.markdown("""
<div class="banner-container">
    <div class="banner-title">Project Anvil: Autonomous Multi-Agent Data Science Platform</div>
    <div class="banner-subtitle">Enterprise Analytics Engine with Deterministic Code Execution and Automated Documentation</div>
</div>
""", unsafe_allow_html=True)

# Prompt Input
col_input, col_url = st.columns([2, 1], gap="medium")

with col_input:
    user_topic = st.text_input(
        "Project Topic or Requirement",
        value=st.session_state.current_topic,
        placeholder="e.g. Student Exam Performance Analysis, Customer Churn, House Price Prediction...",
        help="Describe what project Anvil should build."
    )

with col_url:
    dataset_url = st.text_input(
        "Online Dataset URL (Optional)",
        placeholder="https://raw.githubusercontent.com/.../data.csv",
        help="Optional. If left blank, the Data Agent uses Web-RAG to find and download real datasets automatically."
    )

generate_btn = st.button("Generate Project", type="primary", use_container_width=True)

# ============================================================
# EXECUTION FLOW
# ============================================================

if generate_btn:
    if not user_topic.strip():
        st.warning("Please enter a project topic or requirement.")
        st.stop()

    if DEFAULT_PROVIDER == "ollama":
        ready, msg = check_ollama_status(DEFAULT_MODEL)
        if not ready:
            st.error(f"Ollama is not ready: {msg}")
            st.stop()

    initial_state = {
        "request": user_topic.strip(),
        "dataset_url": dataset_url.strip() if dataset_url else None,
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

    status_card = st.empty()
    progress_bar = st.progress(0)
    accumulated_state = dict(initial_state)

    try:
        status_card.info("**Agent 1 (Data Agent)**: Searching the web with Web-RAG...")
        progress_bar.progress(15)

        for step_update in anvil_graph.stream(initial_state, stream_mode="updates"):
            for node_name, node_output in step_update.items():
                accumulated_state.update(node_output)

                if node_name == "data_agent":
                    progress_bar.progress(45)
                    status_card.info("**Agent 2 (Code Agent)**: Performing 7-part statistical data analysis...")

                elif node_name == "code_agent":
                    progress_bar.progress(80)
                    status_card.info("**Agent 3 (Report Agent)**: Formatting Word (.docx) Project Report...")

                elif node_name == "report_agent":
                    progress_bar.progress(100)
                    status_card.success("**Anvil Pipeline Complete!** All artifacts are ready.")

        # Save to session and history
        st.session_state.result = accumulated_state
        st.session_state.current_topic = user_topic.strip()

        new_history_item = {
            "id": f"proj_{int(time.time())}",
            "topic": user_topic.strip(),
            "timestamp": datetime.now().strftime("%b %d, %H:%M"),
            "result": accumulated_state
        }
        # Prepend to history
        st.session_state.history.insert(0, new_history_item)
        save_history(st.session_state.history)

        st.rerun()

    except Exception as e:
        status_card.error(f"Pipeline Execution Error: {str(e)}")


# ============================================================
# RESULTS DISPLAY (3 SIMPLE DELIVERABLES TABS)
# ============================================================

result = st.session_state.result

if result:
    st.divider()
    st.subheader(f"Deliverables: {st.session_state.get('current_topic', 'Project')}")

    tab_data, tab_code, tab_report = st.tabs([
        "1. Dataset (CSV)",
        "2. Python Code (solution.py)",
        "3. Word Project Report (.docx)"
    ])

    # --------------------------------------------------------
    # TAB 1: DATASET
    # --------------------------------------------------------
    with tab_data:
        st.markdown("### Dataset Details")
        source_url = result.get("dataset_source_url")
        if source_url:
            st.info(f"**Live Web-RAG Source:** [{source_url}]({source_url})")

        raw_summary = result.get("dataset_summary", "No summary available.")
        clean_summary = raw_summary.split("\nFirst 3 Sample Records:")[0].split("First 3 Sample Records:")[0].strip()
        st.text(clean_summary)

        csv_content = result.get("dataset_csv", "")
        if csv_content:
            try:
                df = pd.read_csv(io.StringIO(csv_content))
                st.dataframe(df, width="stretch")
            except Exception:
                st.code(csv_content, language="text")

            col_d1, _ = st.columns([1, 3])
            with col_d1:
                st.download_button(
                    label="Download dataset.csv",
                    data=csv_content,
                    file_name="dataset.csv",
                    mime="text/csv",
                    use_container_width=True
                )

    # --------------------------------------------------------
    # TAB 2: PYTHON CODE
    # --------------------------------------------------------
    with tab_code:
        st.markdown("### Standalone Python Implementation (`solution.py`)")

        code_str = result.get("code", "")
        if code_str:
            st.code(code_str, language="python")

            col_c1, _ = st.columns([1, 3])
            with col_c1:
                st.download_button(
                    label="Download solution.py",
                    data=code_str,
                    file_name="solution.py",
                    mime="text/x-python",
                    use_container_width=True
                )

        exec_out = result.get("execution_output")
        if exec_out:
            with st.expander("View Terminal Execution Output (7-Part Analysis Log)", expanded=True):
                st.code(exec_out, language="text")

    # --------------------------------------------------------
    # TAB 3: WORD PROJECT REPORT
    # --------------------------------------------------------
    with tab_report:
        st.markdown("### Professional Word Project Report (`PROJECT_REPORT.docx`)")
        docx_path_str = result.get("report_docx_path")

        if docx_path_str and os.path.exists(docx_path_str):
            with open(docx_path_str, "rb") as f:
                docx_bytes = f.read()

            pptx_path = GENERATED_DIR / "Project_Anvil_Presentation.pptx"
            pptx_bytes = pptx_path.read_bytes() if pptx_path.exists() else None

            col_r1, col_r2 = st.columns([1, 1])
            with col_r1:
                st.download_button(
                    label="Download Word Report (PROJECT_REPORT.docx)",
                    data=docx_bytes,
                    file_name="PROJECT_REPORT.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True
                )
            if pptx_bytes:
                with col_r2:
                    st.download_button(
                        label="Download Project Presentation (.pptx)",
                        data=pptx_bytes,
                        file_name="Project_Anvil_Presentation.pptx",
                        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                        use_container_width=True
                    )

        st.markdown("#### Executive Report Preview")
        st.markdown(result.get("report_text", "Report generation pending."))

else:
    st.info("Enter your project idea above and click **Generate Project** to build your dataset, Python code, and Word report.")
