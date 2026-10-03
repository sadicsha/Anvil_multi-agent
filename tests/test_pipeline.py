import sys
from pathlib import Path
import pandas as pd
import docx

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.graph import build_graph
from src.agents.report_agent import create_word_document
from src.agents.data_agent import search_duckduckgo_for_csv, get_domain_fallback_dataset
from src.utils import extract_code


def test_code_extraction():
    sample_text = "```python\nimport pandas as pd\nprint('hello')\n```"
    code = extract_code(sample_text)
    assert code == "import pandas as pd\nprint('hello')"
    print("test_code_extraction PASSED")


def test_docx_generation():
    test_docx_path = PROJECT_ROOT / "generated" / "test_report.docx"
    create_word_document(
        title="Automated Test Project",
        executive_summary="This is a test summary for docx generation.",
        dataset_info="Web-RAG Source: https://github.com/.../data.csv\nRows: 10, Columns: 3",
        methodology="Test methodology using pandas and numpy.",
        code_text="def test(): pass",
        execution_results="Test output 100% success",
        conclusion="Test conclusions.",
        output_path=test_docx_path
    )
    assert test_docx_path.exists(), "DOCX file was not created!"
    doc = docx.Document(str(test_docx_path))
    assert len(doc.paragraphs) > 3, "DOCX has too few paragraphs"
    test_docx_path.unlink(missing_ok=True)
    print("test_docx_generation PASSED")


def test_graph_structure():
    graph = build_graph()
    assert graph is not None
    print("test_graph_structure PASSED")


def test_duckduckgo_webrag():
    print("Testing DuckDuckGo Web-RAG live search...")
    df, url = search_duckduckgo_for_csv("telecom churn", max_results=5)
    if df is not None:
        assert isinstance(df, pd.DataFrame)
        assert len(df) >= 5
        assert len(df.columns) >= 2
        assert url is not None and url.startswith("http")
        print(f"test_duckduckgo_webrag PASSED (Retrieved {len(df)} rows from {url[:50]}...)")
    else:
        print("test_duckduckgo_webrag SKIPPED (Network or rate-limited, fallback engaged)")


def test_domain_fallback():
    df_churn = get_domain_fallback_dataset("Customer Churn")
    assert len(df_churn) >= 20
    assert "churn" in df_churn.columns

    df_student = get_domain_fallback_dataset("Student Grades")
    assert len(df_student) >= 20
    assert "final_score" in df_student.columns
    print("test_domain_fallback PASSED")


def test_tavily_webrag():
    from src.agents.data_agent import search_tavily_for_csv
    print("Testing Tavily Web-RAG live search...")
    df, url = search_tavily_for_csv("tata steel stock price csv github", max_results=3)
    if df is not None:
        assert isinstance(df, pd.DataFrame)
        assert len(df) >= 5
        print(f"test_tavily_webrag PASSED (Retrieved {len(df)} rows from {url})")
    else:
        print("test_tavily_webrag SKIPPED (No direct CSV found or fallback engaged)")


def test_task_solution_and_interpretation():
    from src.agents.code_agent import get_task_solution_code
    from src.agents.report_agent import build_lifecycle_sections
    from src.sandbox import run_code_safely

    test_cases = [
        ("predict stock price for tata steel for next 5 days", "Stock Price"),
        ("customer churn prediction in telecom", "Customer Churn"),
        ("Netflix Movies and TV Shows Analysis of positive and negative comments", "Sentiment Analysis"),
        ("predict student final exam score based on study hours", "Predictive Performance"),
        ("credit card fraud detection and risk analysis", "Anomaly Detection")
    ]

    for topic, expected_domain in test_cases:
        df = get_domain_fallback_dataset(topic)
        test_csv_path = PROJECT_ROOT / "generated" / "test_data.csv"
        try:
            df.to_csv(test_csv_path, index=False)

            code = get_task_solution_code(topic, str(test_csv_path))
            passed, out = run_code_safely(code, "", timeout=15)
            assert passed, f"Task '{topic}' failed code execution: {out}"

            # Verify all 7 required analysis sections
            required_sections = [
                "1. DATASET OVERVIEW",
                "2. DATA QUALITY OBSERVATIONS",
                "3. RELEVANT STATISTICAL ANALYSIS",
                "4. IMPORTANT PATTERNS AND RELATIONSHIPS",
                "5. KEY FINDINGS",
                "6. DATA-DRIVEN INSIGHTS",
                "7. PRACTICAL RECOMMENDATIONS"
            ]
            for sec in required_sections:
                assert sec in out, f"Task '{topic}' missing required section '{sec}'!"

            sections = build_lifecycle_sections(topic, "Dataset details", code, out)
            assert len(sections) == 13, f"Expected 13 lifecycle sections, got {len(sections)}"
            assert "1. Project Overview" in sections
            assert "13. Conclusion" in sections
            print(f"Task '{topic[:35]}...' verified 7-part analysis successfully!")
        finally:
            if test_csv_path.exists():
                test_csv_path.unlink(missing_ok=True)

    print("test_task_solution_and_interpretation PASSED")


if __name__ == "__main__":
    print("Running Anvil 3-Agent Unit Tests...")
    test_code_extraction()
    test_docx_generation()
    test_graph_structure()
    test_domain_fallback()
    test_duckduckgo_webrag()
    test_tavily_webrag()
    test_task_solution_and_interpretation()
    print("\nALL 3-AGENT ANVIL TESTS PASSED!")
