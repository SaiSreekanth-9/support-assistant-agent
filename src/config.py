"""Central configuration for the support assistant.

Values come from environment variables / .env. OPENAI_API_KEY is optional:
when it is empty the agent runs in demo (mock) mode using only the Python
standard library. ``python-dotenv`` is an optional dependency, so importing
this module must never fail when it is not installed.
"""
import os

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dotenv is optional in demo mode
    def load_dotenv(*args, **kwargs):  # type: ignore[no-redef]
        """No-op fallback when python-dotenv is not installed."""
        return False


load_dotenv()


class Settings:
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    chat_model: str = os.getenv("CHAT_MODEL", "gpt-4o-mini")
    top_k: int = int(os.getenv("TOP_K", "3"))
    escalation_threshold: float = float(os.getenv("ESCALATION_THRESHOLD", "0.15"))
    docs_dir: str = os.getenv("DOCS_DIR", "data/sample_docs")
    tickets_file: str = os.getenv("TICKETS_FILE", "data/tickets.json")

    @property
    def demo_mode(self) -> bool:
        """True when no API key is set: rule-based + TF-IDF only."""
        return not self.openai_api_key


settings = Settings()
