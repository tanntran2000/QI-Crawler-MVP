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
    if not notice.notice_code and not notice.source_notice_id:
        errors.append("thieu ca notice_code va source_notice_id")
    elif not notice.notice_code:
        warnings.append("notice_code bi thieu; dung source_notice_id cua nguon")
    if not notice.title:
        (errors if strict else warnings).append("title bi thieu")
    if notice.package_price is not None and notice.package_price < 0:
        errors.append("package_price khong duoc am")
    if notice.package_price is None:
        warnings.append("package_price bi thieu")
    if not notice.closing_at:
        warnings.append("closing_at bi thieu")
    if not notice.buyer and not notice.investor:
        warnings.append("buyer/investor bi thieu")
    if not notice.published_at:
        warnings.append("published_at bi thieu")
    if not notice.location:
        warnings.append("location bi thieu")
    if not notice.sector:
        warnings.append("sector bi thieu")
    if not notice.selection_method:
        warnings.append("selection_method bi thieu")

    return ValidationResult(valid=not errors, errors=errors, warnings=warnings)
