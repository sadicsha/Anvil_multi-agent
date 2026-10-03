import zipfile
import shutil
from pathlib import Path
import xml.etree.ElementTree as ET

SOURCE_PPTX = Path(r"C:\Users\SADICSHA\Downloads\Bridging_the_Gap_Executive_Deck.pptx")
DEST_PPTX = Path(r"C:\Users\SADICSHA\anvil\generated\Project_Anvil_Presentation.pptx")
DESKTOP_PPTX = Path(r"C:\Users\SADICSHA\Desktop\Project_Anvil_Presentation.pptx")
DOWNLOADS_PPTX = Path(r"C:\Users\SADICSHA\Downloads\Project_Anvil_Presentation.pptx")

NS_A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
NS_P = "{http://schemas.openxmlformats.org/presentationml/2006/main}"

SLIDE_DATA = {
    1: {
        5: ["AUTONOMOUS MULTI-AGENT DATA SCIENCE & ENGINEERING SYSTEM"],
        6: ["PROJECT ANVIL:"],
        7: ["Autonomous Analytics, Web-RAG & Multi-Agent Architecture"],
        9: ["From Natural Language Intent to Verified Web-RAG Data Discovery, Sandboxed Code Execution, and 13-Stage Word Project Reports."],
        11: ["LangGraph"],
        13: ["Web-RAG"],
        15: ["Sandbox"],
        17: ["Streamlit"],
        18: ["Sadicsha Khandait", "PRN: 25030242046  |  Symbiosis Centre for Information Technology"]
    },
    2: {
        2: ["EXECUTIVE SUMMARY • MULTI-AGENT PARADIGM"],
        3: ["Three Specialized Agents, One Deterministic Analytics Lifecycle"],
        4: ["Across end-to-end data analytics and engineering tasks, the guiding principle is absolute rigor: let generative AI write code, never calculate numbers directly. Agent 1 (Data Agent) discovers data using Web-RAG; Agent 2 (Code Agent) synthesizes and executes math in an isolated sandbox subprocess; and Agent 3 (Report Agent) compiles a 13-stage Word project report—guaranteeing 0% numerical hallucination."],
        7: ["0%"],
        8: ["Numerical Hallucination"],
        9: ["Strict Code Calculation"],
        12: ["<15s"],
        13: ["End-to-End Latency"],
        14: ["Query to 3 Deliverables"],
        17: ["100%"],
        18: ["Test Pass Rate"],
        19: ["tests/test_pipeline.py"],
        22: ["3"],
        23: ["Collaborative Agents"],
        24: ["Data, Code & Report Agents"],
        26: ["THE MULTI-AGENT PLATFORM AT A GLANCE"],
        28: ["Agent 1: Data"],
        29: ["Web-RAG Ingestion"],
        31: ["Agent 2: Code"],
        32: ["Sandbox Execution"],
        34: ["Agent 3: Report"],
        35: ["13-Stage DOCX"],
        37: ["Streamlit UI"],
        38: ["Interactive 3-Tab App"],
        40: ["Project Anvil • Executive Summary"],
        41: ["02"]
    },
    3: {
        2: ["FLOW DIAGRAM & CORE PRINCIPLE"],
        3: ["Decoupling Web-RAG Retrieval from Sandboxed Code Execution"],
        6: ["Step 1: Input"],
        7: ["User Intent"],
        8: ["Natural language requirement &", "intent classification"],
        11: ["Step 2: Web-RAG"],
        12: ["Agent 1: Data"],
        13: ["Tavily & DDG search, GitHub CSV", "streaming & schema profiling"],
        16: ["Step 3: Sandbox"],
        17: ["Agent 2: Code"],
        18: ["Subprocess execution with", "15-second timeout guard"],
        21: ["Step 4: Report"],
        22: ["Agent 3: Word"],
        23: ["13-stage DOCX compilation", "and multi-asset export"],
        25: ["END-TO-END FLOW"],
        26: ["Web-RAG discovers real data ➔ Agent 2 computes verified metrics ➔ Agent 3 compiles the formal Word report."],
        28: ["Project Anvil • End-to-End Flow Diagram"],
        29: ["03"]
    },
    4: {
        2: ["SYSTEM ARCHITECTURE"],
        3: ["5-Layer Multi-Agent Architecture: Interface to Inference"],
        6: ["1. Presentation Layer"],
        7: ["Streamlit UI (3 Tabs)"],
        9: ["User input, dataset explorer, syntax-highlighted code, sandbox terminal log, and DOCX/PPTX downloads."],
        12: ["2. Orchestration Layer"],
        13: ["LangGraph State Machine"],
        15: ["Sequential StateGraph managing shared state, agent coordination, and cyclic fallbacks."],
        18: ["3. Web-RAG Data Layer"],
        19: ["Agent 1: Tavily + DDG"],
        21: ["Live Web-RAG search, raw GitHub CSV streaming, schema typing, and domain fallbacks."],
        24: ["4. Execution Sandbox"],
        25: ["Agent 2: Subprocess Sandbox"],
        27: ["Isolated OS subprocess, 15-second timeout ceiling, memory limits, and UTF-8 telemetry logging."],
        29: ["Project Anvil • 5-Layer System Architecture"],
        30: ["04"]
    },
    5: {
        2: ["ANALYTICAL TASK MATRIX"],
        3: ["Six Domain Archetypes, One Mathematical Standard"],
        5: ["Archetype"],
        7: ["Domain"],
        9: ["Agent 2 Mathematical Engine"],
        11: ["Core Calculated Output"],
        14: ["Time-Series Forecasting"],
        16: ["Capital Markets & Equities"],
        18: ["np.polyfit + Rolling SMA (5/20)"],
        20: ["5-Day Target & Volatility Bounds"],
        23: ["Customer Churn"],
        25: ["Telecom & SaaS Retention"],
        27: ["Cross-Tabs & Risk Propensity"],
        29: ["Defection Rates & Top 20% Cohort"],
        32: ["Sentiment Analysis"],
        34: ["Media & Streaming Feedback"],
        36: ["Lexicon Polarity & N-grams"],
        38: ["Polarity Distribution & Grievances"],
        41: ["Fraud & Anomaly"],
        43: ["Banking & Payment Cards"],
        45: ["IQR Fences + Z-Scores (>2.5)"],
        47: ["Monetary Exposure & Outliers"],
        49: ["Six domain archetypes. One strict standard: every output metric is derived from actual calculated values."],
        51: ["Project Anvil • Analytical Task Matrix"],
        52: ["05"]
    },
    6: {
        2: ["AGENT 1 • DATA AGENT & WEB-RAG ENGINE"],
        3: ["How Web-RAG Ingestion Works: Search, Streaming & Validation"],
        5: ["Agent 1"],
        7: ["Agent 1 Architecture: Dual-Search Web-RAG Ingestion Pipeline"],
        10: ["Dual-Search Web-RAG"],
        11: ["Tavily API (deep domain search) and DuckDuckGo (broad search) query public repositories, extracting raw GitHub CSV URLs into memory."],
        14: ["Schema Typing & Bounding"],
        15: ["Pandas validates headers, resolves target columns, sanitizes missing values, and bounds rows (df.tail 250) for fast execution."],
        18: ["Fail-Safe Domain Generator"],
        19: ["If external networks fail or rate limits trigger, built-in domain generators construct mathematically sound schemas instantly."],
        21: ["Project Anvil • Agent 1 Web-RAG Ingestion Flow"],
        22: ["06"]
    },
    7: {
        2: ["AGENT 2 • CODE AGENT & SUBPROCESS SANDBOX"],
        3: ["How Code Synthesis & Sandbox Execution Works"],
        5: ["Agent 2"],
        7: ["Agent 2 Architecture: Algorithmic Routing & Isolated Subprocess Sandbox"],
        10: ["Task Archetype Synthesis"],
        11: ["Analyzes schema and synthesizes standalone Python code tailored to 6 archetypes (Churn, Stock, Fraud, Sentiment, Regression, Universal)."],
        14: ["Subprocess Sandbox Guard"],
        15: ["Executes code via subprocess.Popen in an isolated OS process with a 15-second hard timeout, preventing infinite loops or server crashes."],
        18: ["Type Safety & Encoding Resilience"],
        19: ["Immunized against pandas StringDtype errors via is_numeric_dtype and reconfigures sys.stdout to UTF-8 for clean terminal logging."],
        21: ["Project Anvil • Agent 2 Code & Sandbox Flow"],
        22: ["07"]
    },
    8: {
        2: ["EMPIRICAL FRAMEWORK • ZERO HALLUCINATION"],
        3: ["The 7-Part Empirical Analysis Contract: From Data to Action"],
        4: ["Execution flow: Raw Data ➔ Python Calculations ➔ Verified Telemetry ➔ Actionable Strategy:"],
        6: ["Standardized 7-Section Output Contract logged directly from sandbox execution:"],
        8: ["Sections 1 & 2: Overview & Quality"],
        9: ["Ingested record counts, column dimensions, missing value counts (NaNs), and duplicate records."],
        11: ["Section 3: Statistical Analysis"],
        12: ["Exact means, medians, standard deviations, distributions, and quantiles (Q1, Q3, P95, P99)."],
        14: ["Sections 4 & 5: Patterns & Findings"],
        15: ["Pearson correlations, cross-tabulations, and pure calculated facts (e.g., 26.5% Baseline Churn)."],
        17: ["Sections 6 & 7: Insights & Recommendations"],
        18: ["Data-driven deductions and practical operational guardrails derived directly from calculated values."],
        20: ["0% Hallucination"],
        21: ["Zero speculative metrics; every finding is backed by mathematical code execution."],
        23: ["Project Anvil • 7-Part Empirical Analysis Flow"],
        24: ["08"]
    },
    9: {
        2: ["AGENT 3 • REPORT AGENT & DOCUMENT ENGINEERING"],
        3: ["How Automated 13-Stage Word Report Generation Works"],
        5: ["Agent 3"],
        7: ["Agent 3 Architecture: Telemetry Parser & Lifecycle Word Document Builder"],
        10: ["13-Stage Lifecycle Compiler"],
        11: ["Assembles formal software engineering documentation: Overview, Problem, Objectives, Architecture, Implementation, Results, Limitations, and Future Scope."],
        14: ["Telemetry & Code Embedding"],
        15: ["Directly embeds the synthesized Python code and the full sandbox execution telemetry table into structured Word tables."],
        18: ["Custom Typography & Styling"],
        19: ["Formatted using custom heading hierarchies (Navy #1F4E79), formal table grid borders, and Consolas monospace code blocks."],
        21: ["Project Anvil • Agent 3 Document Generation Flow"],
        22: ["09"]
    },
    10: {
        2: ["USER INTERFACE • 3-TAB DASHBOARD"],
        3: ["Streamlit Dashboard: Instant Interactive Deliverables"],
        5: ["Frontend UI"],
        7: ["Streamlit Frontend — Seamless 3-Tab Operational Workflow"],
        10: ["Tab 1: Dataset Explorer"],
        11: ["Interactive dataframe viewer with schema column types, row counts, provenance attribution, and CSV download."],
        14: ["Tab 2: Python Code & Logs"],
        15: ["Full syntax-highlighted solution.py script alongside an expandable terminal viewer showing live 7-part sandbox logs."],
        18: ["Tab 3: Word & PPTX Downloads"],
        19: ["One-click download buttons for PROJECT_REPORT.docx and Project_Anvil_Presentation.pptx alongside lifecycle Markdown preview."],
        21: ["Project Anvil • User Interface Architecture"],
        22: ["10"]
    },
    11: {
        2: ["PERFORMANCE METRICS & BENCHMARKS"],
        3: ["The Numbers Behind the Anvil Multi-Agent Platform"],
        6: ["100%"],
        7: ["Test Suite Pass Rate"],
        8: ["tests/test_pipeline.py"],
        11: ["0%"],
        12: ["Numerical Hallucination"],
        13: ["Code-driven verification"],
        16: ["<15s"],
        17: ["End-to-End Pipeline"],
        18: ["Query to 3 deliverables"],
        21: ["13"],
        22: ["Report Lifecycle Stages"],
        23: ["Full engineering DOCX"],
        26: ["7"],
        27: ["Analysis Sections"],
        28: ["Standardized contract"],
        31: ["6"],
        32: ["Domain Archetypes"],
        33: ["Finance, Telecom, Fintech"],
        36: ["15s"],
        37: ["Sandbox Timeout Guard"],
        38: ["Subprocess safety ceiling"],
        41: ["100%"],
        42: ["Local Processing Parity"],
        43: ["Zero external webhooks"],
        45: ["Project Anvil • Performance Benchmarks"],
        46: ["11"]
    },
    12: {
        2: ["ARCHITECTURAL PARADIGM SHIFTS"],
        3: ["Three Shifts Defining Production-Grade Autonomous AI"],
        7: ["01"],
        8: ["Probabilistic to Deterministic"],
        9: ["Decoupling calculation from language eliminates hallucination. The LLM writes the code; deterministic engines execute the math."],
        13: ["02"],
        14: ["Subprocess Sandboxing as a Safety Primitive"],
        15: ["Isolating code execution into dedicated subprocesses with strict timeouts prevents infinite loops, crashes, and memory leaks."],
        19: ["03"],
        20: ["Multi-Agent Specialization over Monoliths"],
        21: ["Dividing workflows into Data, Code, and Report agents orchestrated by LangGraph ensures modularity, auditability, and resilience."],
        23: ["Project Anvil • Architectural Shifts"],
        24: ["12"]
    },
    13: {
        2: ["RECOMMENDATIONS • NEXT STEPS"],
        3: ["Where Project Anvil Goes Next: The Enterprise Roadmap"],
        7: ["Automated ML Training"],
        8: ["scikit-learn, XGBoost & LightGBM", "Automated cross-validation tuning", "ROC-AUC & F1-score evaluation"],
        12: ["Enterprise Cloud Warehouses"],
        13: ["Snowflake, BigQuery & Databricks", "Direct SQL schema extraction", "Streaming data ingestion"],
        17: ["Scheduled Intelligence"],
        18: ["Daily / weekly cron executions", "CRM automated alerts & triggers", "Automated Slack/Email dispatch"],
        22: ["Multi-Format Export"],
        23: ["Automated PPTX presentation deck", "Executive PDF summaries", "Interactive HTML widgets"],
        25: ["Project Anvil • Strategic Roadmap"],
        26: ["13"]
    },
    14: {
        4: ["CLOSING & Q&A"],
        5: ["Thank You"],
        6: ["Three specialized agents. One deterministic execution philosophy. Verified data science deliverables in seconds."],
        8: ["100%"],
        9: ["Test Pass Rate"],
        11: ["0%"],
        12: ["Hallucination"],
        14: ["13"],
        15: ["DOCX Stages"],
        17: ["<15s"],
        18: ["Pipeline Runtime"],
        20: ["Sadicsha Khandait", "PRN: 25030242046", "Symbiosis Centre for Information Technology"],
        24: ["Project Anvil • Autonomous Multi-Agent Platform"],
        25: ["14"]
    }
}

def update_shape_text(sp, new_paras):
    txBody = sp.find(f"{NS_P}txBody")
    if txBody is None:
        return
    p_elements = txBody.findall(f"{NS_A}p")
    if not p_elements:
        return

    # Keep first paragraph template
    first_p = p_elements[0]
    pPr = first_p.find(f"{NS_A}pPr")
    first_r = first_p.find(f"{NS_A}r")
    rPr = first_r.find(f"{NS_A}rPr") if first_r is not None else None

    # Remove all existing paragraphs
    for p_elem in list(p_elements):
        txBody.remove(p_elem)

    # Recreate paragraphs with the new text
    for para_text in new_paras:
        new_p = ET.Element(f"{NS_A}p")
        if pPr is not None:
            new_p.append(ET.fromstring(ET.tostring(pPr)))
        
        new_r = ET.Element(f"{NS_A}r")
        if rPr is not None:
            new_r.append(ET.fromstring(ET.tostring(rPr)))
        
        t_elem = ET.Element(f"{NS_A}t")
        t_elem.text = para_text
        new_r.append(t_elem)
        new_p.append(new_r)
        txBody.append(new_p)


def build_presentation():
    print(f"Reading template from {SOURCE_PPTX}...")
    with zipfile.ZipFile(SOURCE_PPTX, 'r') as zin:
        all_files = {name: zin.read(name) for name in zin.namelist()}

    DEST_PPTX.parent.mkdir(parents=True, exist_ok=True)

    for slide_num, shape_map in SLIDE_DATA.items():
        slide_xml_path = f"ppt/slides/slide{slide_num}.xml"
        if slide_xml_path not in all_files:
            continue
        
        root = ET.fromstring(all_files[slide_xml_path])
        sp_idx = 0
        for sp in root.iter(f"{NS_P}sp"):
            sp_idx += 1
            if sp_idx in shape_map:
                update_shape_text(sp, shape_map[sp_idx])
        
        all_files[slide_xml_path] = ET.tostring(root, encoding="utf-8", xml_declaration=True)
        print(f"Processed slide {slide_num} ({len(shape_map)} shapes updated).")

    # Save to generated/Project_Anvil_Presentation.pptx
    with zipfile.ZipFile(DEST_PPTX, 'w', compression=zipfile.ZIP_DEFLATED) as zout:
        for name, data in all_files.items():
            zout.writestr(name, data)

    print(f"Successfully generated: {DEST_PPTX}")

    # Copy to Desktop and Downloads for instant convenience
    try:
        shutil.copy(DEST_PPTX, DESKTOP_PPTX)
        print(f"Copied to Desktop: {DESKTOP_PPTX}")
    except Exception as e:
        print(f"Desktop copy skipped: {e}")

    try:
        shutil.copy(DEST_PPTX, DOWNLOADS_PPTX)
        print(f"Copied to Downloads: {DOWNLOADS_PPTX}")
    except Exception as e:
        print(f"Downloads copy skipped: {e}")

if __name__ == "__main__":
    build_presentation()
