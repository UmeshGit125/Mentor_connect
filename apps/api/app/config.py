import os
from dataclasses import dataclass
from pathlib import Path

# Lives inside apps/api so it ships with the deployed function.
DEFAULT_XLSX = Path(__file__).resolve().parents[1] / "data" / "Mentor_Sample_50_Anonymised.xlsx"


@dataclass(frozen=True)
class Settings:
    database_url: str
    admin_password: str
    allowed_origins: list[str]
    mentors_xlsx: Path
    llm_api_key: str
    use_live_ai: bool
    auto_setup: bool


def get_settings() -> Settings:
    origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000")
    return Settings(
        database_url=os.environ.get("DATABASE_URL", "sqlite:///./mentor_connect.db"),
        admin_password=os.environ.get("ADMIN_PASSWORD", "change-me"),
        allowed_origins=[o.strip() for o in origins.split(",") if o.strip()],
        mentors_xlsx=Path(os.environ.get("MENTORS_XLSX", DEFAULT_XLSX)),
        llm_api_key=os.environ.get("OPENROUTER_API_KEY", "").strip(),
        use_live_ai=os.environ.get("USE_LIVE_AI", "1").strip() != "0",
        # On a serverless host set AUTO_SETUP=0 and run `python -m app.seed` once instead.
        auto_setup=os.environ.get("AUTO_SETUP", "1").strip() != "0",
    )
