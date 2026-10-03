from typing import TypedDict, Optional


class AnvilState(TypedDict):
    # User inputs
    request: str
    dataset_url: Optional[str]

    # Agent 1: Data outputs
    dataset_csv: Optional[str]
    dataset_summary: Optional[str]
    dataset_path: Optional[str]
    dataset_source_url: Optional[str]

    # Agent 2: Code outputs
    code: Optional[str]
    code_path: Optional[str]
    execution_output: Optional[str]

    # Agent 3: Report outputs
    report_text: Optional[str]
    report_docx_path: Optional[str]
    solution_summary: Optional[str]

    # Model settings
    model_name: Optional[str]
    provider: Optional[str]
    api_key: Optional[str]