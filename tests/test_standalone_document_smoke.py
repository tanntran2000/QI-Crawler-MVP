from __future__ import annotations

from pathlib import Path

from qi_crawler.config import AppConfig
from qi_crawler.standalone_smoke import _document_intake_smoke


def test_document_smoke_covers_workspace_integrity_without_network(tmp_path: Path) -> None:
    config = AppConfig.model_validate(
        {
            "allowed_domains": ["smoke.example"],
            "compliance": {"obey_robots_txt": False},
            "storage": {
                "database_url": f"sqlite:///{tmp_path / 'smoke.db'}",
                "document_dir": str(tmp_path / "documents"),
                "download_dir": str(tmp_path / "downloads"),
                "report_dir": str(tmp_path / "reports"),
                "rejects_dir": str(tmp_path / "rejects"),
            },
        }
    )
    config.storage.document_dir.mkdir(parents=True)
    config.storage.download_dir.mkdir(parents=True)

    result = _document_intake_smoke(config, tmp_path)

    assert result["pdf_docx_xlsx_zip"] == 4
    assert result["duplicate"] == "DUPLICATE"
    assert result["new_version"] == 5
    assert result["mismatch_blocked"] is True
    assert result["taxonomy"] == "VERIFIED"
    assert result["web_attachment_downloaded"] == 1
    assert result["persisted_documents"] == 6
