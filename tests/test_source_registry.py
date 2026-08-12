from __future__ import annotations

import pytest

from qi_crawler.compliance import AccessDenied, AccessPolicy
from qi_crawler.config import AppConfig
from qi_crawler.source_adapters import CotecconsAdapter, EGPAdapter, SourceRegistry


def _config() -> AppConfig:
    return AppConfig.model_validate(
        {
            "sources": {
                "egp": {
                    "enabled": True,
                    "priority": 1,
                    "domain": "muasamcong.mpi.gov.vn",
                    "adapter": "egp",
                },
                "coteccons": {
                    "enabled": True,
                    "priority": 2,
                    "domain": "ebidding.coteccons.vn",
                    "adapter": "coteccons",
                },
            }
        }
    )


def test_egp_domain_allowed() -> None:
    config = _config()
    AccessPolicy(config).validate_domain(
        "https://muasamcong.mpi.gov.vn/vi/web/guest/contractor-selection?notifyNo=IB260001"
    )
    assert isinstance(
        SourceRegistry(config).require_adapter(
            "https://muasamcong.mpi.gov.vn/vi/web/guest/contractor-selection?notifyNo=IB260001"
        ),
        EGPAdapter,
    )


def test_coteccons_domain_allowed() -> None:
    config = _config()
    AccessPolicy(config).validate_domain("https://ebidding.coteccons.vn/Index/ChiTiet/2607301")
    assert isinstance(
        SourceRegistry(config).require_adapter(
            "https://ebidding.coteccons.vn/Index/ChiTiet/2607301"
        ),
        CotecconsAdapter,
    )


def test_unknown_domain_rejected() -> None:
    config = _config()
    with pytest.raises(AccessDenied, match="allowlist"):
        AccessPolicy(config).validate_domain("https://unknown-tender.example/notice/1")
    with pytest.raises(ValueError, match="nguon dang bat"):
        SourceRegistry(config).require_adapter("https://unknown-tender.example/notice/1")
