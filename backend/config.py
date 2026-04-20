from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


def _split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _split_pipe(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split("|") if item.strip()]


@dataclass
class Settings:
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    claude_model: str = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")
    claude_model_copy: str = os.getenv("CLAUDE_MODEL_COPY", "claude-opus-4-7")

    google_service_account_file: str = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "")
    google_drive_folder_id: str = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "")

    news_urls: list[str] = field(default_factory=lambda: _split_csv(os.getenv("NEWS_URLS")))
    google_news_queries: list[str] = field(
        default_factory=lambda: _split_pipe(os.getenv("GOOGLE_NEWS_QUERIES"))
    )
    ig_profiles: list[str] = field(default_factory=lambda: _split_csv(os.getenv("IG_PROFILES")))

    tz: str = os.getenv("TZ", "America/Sao_Paulo")
    output_dir: Path = field(
        default_factory=lambda: Path(os.getenv("OUTPUT_DIR", str(ROOT / "backend" / "output"))).resolve()
    )
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    def ensure_ready(self) -> None:
        if not self.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY ausente no .env")
        self.output_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()
