from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ComplianceConfig(BaseModel):
    obey_robots_txt: bool = True
    stop_on_captcha: bool = True
    identify_user_agent: str = "EGPResearchCrawler/0.2 (contact: replace-me@example.com)"


class CrawlConfig(BaseModel):
    requests_per_minute: int = Field(default=12, ge=1, le=120)
    concurrency: int = Field(default=1, ge=1, le=8)
    request_timeout_seconds: int = Field(default=30, ge=5, le=180)
    browser_timeout_seconds: int = Field(default=45, ge=5, le=180)
    max_retries: int = Field(default=3, ge=0, le=10)
    use_browser_fallback: bool = True
    render_wait_ms: int = Field(default=2500, ge=0, le=30000)
    max_pages_per_run: int = Field(default=100, ge=1, le=10000)


class StorageConfig(BaseModel):
    database_url: str = "sqlite:///./data/egp.db"
    download_dir: Path = Path("./data/downloads")
    discovery_dir: Path = Path("./data/discovery")
    raw_dir: Path = Path("./data/raw")
    rejects_dir: Path = Path("./data/rejects")
    report_dir: Path = Path("./data/reports")
    download_attachments: bool = True
    max_attachment_mb: int = Field(default=50, ge=1, le=500)
    allowed_attachment_extensions: list[str] = Field(
        default_factory=lambda: [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".zip"]
    )

    @field_validator("allowed_attachment_extensions")
    @classmethod
    def normalize_extensions(cls, value: list[str]) -> list[str]:
        return sorted({ext.lower() if ext.startswith(".") else f".{ext.lower()}" for ext in value})


class SelectorConfig(BaseModel):
    # Trang danh sách / tìm kiếm
    search_input: str | None = None
    search_button: str | None = None
    result_ready: str | None = None
    list_item: str = "a[href]"
    detail_link: str = "a"
    next_page: str = "a[aria-label='Next']"
    page_ready: str = "body"

    # Trang chi tiết / tệp đính kèm. Đây là cấu hình theo từng nguồn, không hard-code.
    attachment_rows: str | None = None
    attachment_download_button: str | None = None
    attachment_name: str | None = None


class ReportingConfig(BaseModel):
    days_ahead: int = Field(default=7, ge=1, le=90)
    smtp_host: str | None = None
    smtp_port: int = Field(default=587, ge=1, le=65535)
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_use_tls: bool = True
    email_from: str | None = None
    email_to: list[str] = Field(default_factory=list)

    @field_validator("email_to")
    @classmethod
    def normalize_recipients(cls, value: list[str]) -> list[str]:
        return sorted({item.strip() for item in value if item.strip()})


class AppConfig(BaseModel):
    project_name: str = "egp-public-crawler"
    allowed_domains: list[str] = Field(default_factory=lambda: ["muasamcong.mpi.gov.vn"])
    seed_urls: list[str] = Field(default_factory=list)
    compliance: ComplianceConfig = Field(default_factory=ComplianceConfig)
    crawl: CrawlConfig = Field(default_factory=CrawlConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    selectors: SelectorConfig = Field(default_factory=SelectorConfig)
    reporting: ReportingConfig = Field(default_factory=ReportingConfig)

    @field_validator("allowed_domains")
    @classmethod
    def normalize_domains(cls, value: list[str]) -> list[str]:
        return sorted({item.lower().strip(". ") for item in value if item.strip()})


class EnvSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="EGP_", env_file=".env", extra="ignore")
    database_url: str | None = None
    config_path: Path = Path("./config.yaml")
    log_level: str = "INFO"
    smtp_password: str | None = None
    smtp_username: str | None = None


def load_config(path: Path | str | None = None) -> AppConfig:
    env = EnvSettings()
    config_path = Path(path or env.config_path)
    if not config_path.exists():
        raise FileNotFoundError(
            f"Không tìm thấy {config_path}. Sao chép config.example.yaml thành config.yaml trước."
        )
    raw: dict[str, Any] = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    config = AppConfig.model_validate(raw)
    if env.database_url:
        config.storage.database_url = env.database_url
    if env.smtp_password:
        config.reporting.smtp_password = env.smtp_password
    if env.smtp_username:
        config.reporting.smtp_username = env.smtp_username

    for directory in (
        config.storage.download_dir,
        config.storage.discovery_dir,
        config.storage.raw_dir,
        config.storage.rejects_dir,
        config.storage.report_dir,
    ):
        directory.mkdir(parents=True, exist_ok=True)
    return config
