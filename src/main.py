import sys
from pathlib import Path

# Fix Windows console encoding
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.graph import build_graph


def run_cli(request: str, dataset_url: str = None, model_name: str = None):
    """
    Run the 3-Agent Anvil pipeline directly from CLI.
    """
    print("=" * 60)
    print("ANVIL 3-AGENT PIPELINE")
    print("=" * 60)
    print(f"Project Topic: {request}")
    if dataset_url:
        print(f"Online Dataset URL: {dataset_url}")
    print()

    graph = build_graph()

    initial_state = {
        "request": request,
        "dataset_url": dataset_url,
        "dataset_csv": None,
        "dataset_summary": None,
        "dataset_path": None,
        "code": None,
        "code_path": None,
        "execution_output": None,
        "report_text": None,
        "report_docx_path": None,
        "model_name": model_name,
        "provider": "ollama",
        "api_key": None
    }

    state = dict(initial_state)

    for update in graph.stream(initial_state, stream_mode="updates"):
        for node_name, output in update.items():
            state.update(output)
            print(f"-> Completed: {node_name}")

    print("\n" + "=" * 60)
    print("ARTIFACTS GENERATED:")
    print("=" * 60)
    print(f"1. Dataset CSV:   {state.get('dataset_path')}")
    print(f"2. Python Code:   {state.get('code_path')}")
    print(f"3. Word Report:   {state.get('report_docx_path')}")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    topic = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Student Exam Performance Analysis"
    sys.exit(run_cli(topic))
