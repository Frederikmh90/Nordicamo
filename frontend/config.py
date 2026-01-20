import os


def get_api_base_url() -> str:
    """
    Resolve the FastAPI base URL for the Streamlit dashboard.

    Priority:
    - env var NAMO_API_BASE_URL
    - default to local dev
    """
    return os.getenv("NAMO_API_BASE_URL", "http://127.0.0.1:8001").rstrip("/")
