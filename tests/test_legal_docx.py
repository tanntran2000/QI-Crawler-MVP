from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest
from docx import Document
from sqlalchemy import func, select

from qi_crawler.db import Database
from qi_crawler.market_intelligence.candidate_review import CandidateReviewService
from qi_crawler.market_intelligence.khmt_contract import load_sanitized_khmt_fixture
from qi_crawler.market_intelligence.legal_docx import (
    LEGAL_FIELD_HEADERS,
    LegalDocxCollisionError,
    export_confirmed_legal_docx,
)
from qi_crawler.models import CandidateReviewEvent

FIXTURE = Path(__file__).parent / "fixtures" / "khmt" / "khmt_sanitized_golden.json"


def _packages():
    packages = load_sanitized_khmt_fixture(FIXTURE)[1]
    return tuple(
        replace(
            package,
            raw_fields={
                **package.raw_fields,
                "QUA MẠNG": "Qua mạng",
                "SƠ TUYỂN": "Không sơ tuyển",
                "PHƯƠNG THỨC": "Một giai đoạn một túi hồ sơ",
                "ĐỊA BÀN": "Thành phố Mẫu",
            },
            provenance={
                **package.provenance,
                "source_filename": package.plan.import_batch.source_filename,
                "source_sha256": package.plan.import_batch.source_sha256,
                "sheet": package.plan.import_batch.sheet,
                "source_row": package.source_row,
            },
        )
        for package in packages
    )


def _distinct_bases(packages):
    result = []
    for index, package in enumerate(packages, start=1):
        base = f"PL-SYN-LEGAL-{index:03d}"
        plan = replace(
            package.plan,
            plan_id_raw=f"{base}-00",
            plan_base_id=base,
            plan_revision="00",
        )
        result.append(replace(package, plan=plan))
    return tuple(result)


def _service(tmp_path: Path) -> tuple[Database, CandidateReviewService]:
    database = Database(f"sqlite:///{tmp_path / 'legal-docx.db'}")
    return database, CandidateReviewService(database)


def _table_rows(path: Path) -> tuple[tuple[str, str], ...]:
    table = Document(path).tables[0]
    return tuple((row.cells[0].text, row.cells[1].text) for row in table.rows)


def test_three_latest_confirmed_packages_generate_exact_legal_docx_contract(
    tmp_path: Path,
) -> None:
    _, service = _service(tmp_path)
    packages = _distinct_bases(_packages()[:3])
    for package in packages:
        service.record_decision(package, decision="CONFIRMED", reviewer="Team Bid")

    result = export_confirmed_legal_docx(service, packages, output_dir=tmp_path / "out")

    assert len(result) == 3
    assert [item.output.name for item in result] == [
        "ThongTin_PL-SYN-LEGAL-001.docx",
        "ThongTin_PL-SYN-LEGAL-002.docx",
        "ThongTin_PL-SYN-LEGAL-003.docx",
    ]
    rows = _table_rows(result[0].output)
    assert tuple(label for label, _ in rows) == LEGAL_FIELD_HEADERS
    assert rows[0][1] == packages[0].plan.plan_id_raw
    assert rows[1][1] == packages[0].raw_fields["GÓI TIN"]
    assert rows[2][1] == packages[0].raw_fields["TÊN GÓI THẦU"]
    assert rows[4][1] == packages[0].raw_fields["NỘI DUNG PHÊ DUYỆT"]
    assert rows[8][1] == "Qua mạng"
    assert rows[14][1] == "Thành phố Mẫu"


def test_rejected_latest_state_is_excluded_from_next_legal_export(tmp_path: Path) -> None:
    _, service = _service(tmp_path)
    packages = _distinct_bases(_packages()[:3])
    for package in packages:
        service.record_decision(package, decision="CONFIRMED", reviewer="Team Bid")
    service.record_decision(packages[1], decision="REJECTED", reviewer="Team Bid")

    result = export_confirmed_legal_docx(service, packages, output_dir=tmp_path / "out")

    assert len(result) == 2
    assert {item.output.name for item in result} == {
        "ThongTin_PL-SYN-LEGAL-001.docx",
        "ThongTin_PL-SYN-LEGAL-003.docx",
    }


def test_missing_unsupported_fields_are_blank_and_unicode_survives_reopen(
    tmp_path: Path,
) -> None:
    _, service = _service(tmp_path)
    package = _distinct_bases(_packages()[:1])[0]
    package = replace(
        package,
        package_name="Gói thầu tiếng Việt — thử nghiệm",
        raw_fields={
            **package.raw_fields,
            "TÊN GÓI THẦU": "Gói thầu tiếng Việt — thử nghiệm",
            "QUA MẠNG": None,
            "SƠ TUYỂN": None,
            "PHƯƠNG THỨC": None,
            "ĐỊA BÀN": None,
        },
    )
    service.record_decision(package, decision="CONFIRMED", reviewer="Người duyệt")

    result = export_confirmed_legal_docx(service, (package,), output_dir=tmp_path / "out")
    rows = _table_rows(result[0].output)

    assert rows[2][1] == "Gói thầu tiếng Việt — thử nghiệm"
    assert rows[8][1] == rows[9][1] == rows[10][1] == rows[14][1] == ""


def test_revision_and_source_identity_remain_independent(tmp_path: Path) -> None:
    _, service = _service(tmp_path)
    revision_00, _, revision_01 = _packages()[:3]
    service.record_decision(revision_00, decision="CONFIRMED", reviewer="Team Bid")
    service.record_decision(revision_01, decision="CONFIRMED", reviewer="Team Bid")

    first = export_confirmed_legal_docx(service, (revision_00,), output_dir=tmp_path / "rev00")
    second = export_confirmed_legal_docx(service, (revision_01,), output_dir=tmp_path / "rev01")

    assert _table_rows(first[0].output)[0][1] == "PL-SYN-2026-001-00"
    assert _table_rows(second[0].output)[0][1] == "PL-SYN-2026-001-01"


def test_filename_collision_fails_without_overwrite(tmp_path: Path) -> None:
    _, service = _service(tmp_path)
    package = _distinct_bases(_packages()[:1])[0]
    service.record_decision(package, decision="CONFIRMED", reviewer="Team Bid")
    output_dir = tmp_path / "out"
    first = export_confirmed_legal_docx(service, (package,), output_dir=output_dir)[0].output
    original = first.read_bytes()

    with pytest.raises(LegalDocxCollisionError):
        export_confirmed_legal_docx(service, (package,), output_dir=output_dir)

    assert first.read_bytes() == original


def test_legal_export_does_not_mutate_review_history_or_database(tmp_path: Path) -> None:
    database, service = _service(tmp_path)
    package = _distinct_bases(_packages()[:1])[0]
    service.record_decision(package, decision="CONFIRMED", reviewer="Team Bid")
    with database.session() as session:
        before = session.scalar(select(func.count(CandidateReviewEvent.id)))

    export_confirmed_legal_docx(service, (package,), output_dir=tmp_path / "out")

    with database.session() as session:
        after = session.scalar(select(func.count(CandidateReviewEvent.id)))
    assert before == after == 1
