from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from qi_crawler.market_intelligence.opportunity_contract import (
    OpportunityCandidate,
    OpportunityContractError,
    OpportunityIdentity,
    OpportunityIdentityNamespace,
    OpportunityImportBatch,
    OpportunitySourceType,
)


def _batch(source_type: OpportunitySourceType = OpportunitySourceType.KHMT) -> OpportunityImportBatch:
    return OpportunityImportBatch(
        source_filename="sanitized.xlsx",
        source_sha256="a" * 64,
        sheet="Sheet1",
        imported_at=datetime(2026, 8, 23, tzinfo=UTC),
        schema_version="1",
        source_type=source_type,
    )


def _candidate(
    *,
    identity: OpportunityIdentity | None = None,
    batch: OpportunityImportBatch | None = None,
    provenance: dict[str, object] | None = None,
) -> OpportunityCandidate:
    return OpportunityCandidate(
        identity=identity or OpportunityIdentity.from_raw("PL2600245672-02"),
        import_batch=batch or _batch(),
        source_row=7,
        package_name="Gói mẫu",
        project="Dự án mẫu",
        package_price_raw="123,45",
        package_price=Decimal("123.45"),
        funding_source="Ngân sách mẫu",
        location_detail_raw="TP.HCM",
        raw_fields={"TÊN GÓI THẦU": "Gói mẫu"},
        provenance=provenance
        or {
            "source_filename": "sanitized.xlsx",
            "source_sha256": "a" * 64,
            "sheet": "Sheet1",
            "source_row": 7,
        },
    )


def test_valid_pl_identity_preserves_raw_base_revision_and_namespace() -> None:
    identity = OpportunityIdentity.from_raw("PL2600245672-02")

    assert identity.raw_id == "PL2600245672-02"
    assert identity.base_id == "PL2600245672"
    assert identity.revision == "02"
    assert identity.namespace is OpportunityIdentityNamespace.PL


def test_valid_ib_identity_preserves_raw_base_revision_and_namespace() -> None:
    identity = OpportunityIdentity.from_raw("IB2600463290-00")

    assert identity.raw_id == "IB2600463290-00"
    assert identity.base_id == "IB2600463290"
    assert identity.revision == "00"
    assert identity.namespace is OpportunityIdentityNamespace.IB


def test_same_ib_lineage_different_revisions_remain_distinct_identities() -> None:
    revision_00 = OpportunityIdentity.from_raw("IB2600462391-00")
    revision_01 = OpportunityIdentity.from_raw("IB2600462391-01")

    assert revision_00.base_id == revision_01.base_id == "IB2600462391"
    assert revision_00.revision == "00"
    assert revision_01.revision == "01"
    assert revision_00.raw_id == "IB2600462391-00"
    assert revision_01.raw_id == "IB2600462391-01"
    assert revision_00 != revision_01


def test_identity_rejects_raw_base_revision_mismatch() -> None:
    with pytest.raises(OpportunityContractError, match="identity"):
        OpportunityIdentity(
            raw_id="IB2600463290-00",
            base_id="IB2600463290",
            revision="01",
            namespace=OpportunityIdentityNamespace.IB,
        )


@pytest.mark.parametrize(
    ("source_type", "identity"),
    [
        (
            OpportunitySourceType.KHMT,
            OpportunityIdentity.from_raw("IB2600463290-00"),
        ),
        (
            OpportunitySourceType.TBMT,
            OpportunityIdentity.from_raw("PL2600245672-02"),
        ),
    ],
)
def test_candidate_rejects_source_namespace_mismatch(
    source_type: OpportunitySourceType,
    identity: OpportunityIdentity,
) -> None:
    with pytest.raises(OpportunityContractError, match="namespace"):
        _candidate(identity=identity, batch=_batch(source_type))


def test_import_batch_rejects_invalid_sha() -> None:
    with pytest.raises(OpportunityContractError, match="SHA-256"):
        OpportunityImportBatch(
            source_filename="sanitized.xlsx",
            source_sha256="not-a-sha",
            sheet="Sheet1",
            imported_at=datetime.now(UTC),
            schema_version="1",
            source_type=OpportunitySourceType.KHMT,
        )


def test_candidate_rejects_non_positive_source_row() -> None:
    with pytest.raises(OpportunityContractError, match="source_row"):
        OpportunityCandidate(
            identity=OpportunityIdentity.from_raw("PL2600245672-02"),
            import_batch=_batch(),
            source_row=0,
            package_name="Gói mẫu",
            project=None,
            package_price_raw=None,
            package_price=None,
            funding_source=None,
            location_detail_raw=None,
            raw_fields={},
            provenance={"source_filename": "sanitized.xlsx"},
        )


def test_candidate_preserves_source_fields_and_provenance() -> None:
    candidate = _candidate()

    assert candidate.raw_fields["TÊN GÓI THẦU"] == "Gói mẫu"
    assert candidate.provenance["source_filename"] == "sanitized.xlsx"
    assert candidate.provenance["source_row"] == 7
    assert candidate.identity.raw_id == "PL2600245672-02"
    assert candidate.import_batch.sheet == "Sheet1"


def test_candidate_rejects_mismatched_source_row_provenance() -> None:
    with pytest.raises(OpportunityContractError, match="provenance"):
        _candidate(
            provenance={
                "source_sha256": "a" * 64,
                "sheet": "Sheet1",
                "source_row": 999,
            }
        )


def test_candidate_rejects_mismatched_sheet_provenance() -> None:
    with pytest.raises(OpportunityContractError, match="provenance"):
        _candidate(
            provenance={
                "source_sha256": "a" * 64,
                "sheet": "Other",
                "source_row": 7,
            }
        )


def test_candidate_rejects_mismatched_source_sha_provenance() -> None:
    with pytest.raises(OpportunityContractError, match="provenance"):
        _candidate(
            provenance={
                "source_sha256": "b" * 64,
                "sheet": "Sheet1",
                "source_row": 7,
            }
        )


def test_tbmt_ib_candidate_is_source_neutral_without_pl_conversion() -> None:
    candidate = _candidate(
        identity=OpportunityIdentity.from_raw("IB2600463290-00"),
        batch=_batch(OpportunitySourceType.TBMT),
    )

    assert candidate.import_batch.source_type is OpportunitySourceType.TBMT
    assert candidate.identity.namespace is OpportunityIdentityNamespace.IB
    assert candidate.identity.base_id == "IB2600463290"
