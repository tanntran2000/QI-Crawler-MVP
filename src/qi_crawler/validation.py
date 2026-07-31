from __future__ import annotations

from dataclasses import dataclass, field

from .parser import ParsedNotice


@dataclass(slots=True)
class ValidationResult:
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def validate_notice(notice: ParsedNotice, strict: bool = False) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    if not notice.source_url:
        errors.append("source_url bi thieu")
    if not notice.notice_code:
        (errors if strict else warnings).append("notice_code bi thieu")
    if not notice.title:
        (errors if strict else warnings).append("title bi thieu")
    if notice.package_price is not None and notice.package_price < 0:
        errors.append("package_price khong duoc am")
    if not notice.closing_at:
        warnings.append("closing_at bi thieu")

    return ValidationResult(valid=not errors, errors=errors, warnings=warnings)
