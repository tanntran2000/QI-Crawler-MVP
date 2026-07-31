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
        errors.append("source_url bị thiếu")
    if not notice.notice_code:
        (errors if strict else warnings).append("notice_code bị thiếu")
    if not notice.title:
        (errors if strict else warnings).append("title bị thiếu")
    if notice.package_price is not None and notice.package_price < 0:
        errors.append("package_price không được âm")
    if not notice.closing_at:
        warnings.append("closing_at bị thiếu")

    return ValidationResult(valid=not errors, errors=errors, warnings=warnings)
