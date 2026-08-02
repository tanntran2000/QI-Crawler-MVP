from __future__ import annotations

from . import __version__

RELEASE_DATE = "2026-08-02"

BEGINNER_HIGHLIGHTS = (
    "Dung xep-hang de cham Opportunity Priority Score, khong phai xac suat trung thau.",
    "Bao cao phan loai PRIORITY, REVIEW, SKIP hoac INSUFFICIENT_DATA.",
    "Cac lenh -help va -adv nay cung hien phien ban, thay doi moi va noi xem tai lieu day du.",
    "MVP hien van dung Terminal; Web UI nut bam da duoc ghi nhan cho phien ban sau.",
)

ADVANCED_HIGHLIGHTS = (
    "Keyword ho tro trong so, dong nghia, AND/OR/NOT va chuan hoa tieng Viet.",
    "Metadata chi tiet, canh bao deadline va chong trung theo ma thong bao + phien ban.",
    "CSV/XLSX duoc chan formula injection; file du lieu noi bo bi loai khoi Git.",
    "Kiem thu dong bo bat buoc CHANGELOG, huong dan, -help va -adv cung mot phien ban.",
    "Roadmap UI: giao dien web cuc bo goi lai CLI/API, khong loai bo luong tu dong hoa cu.",
)


def render_release_highlights(*, advanced: bool = False) -> str:
    lines = [f"CAP NHAT MOI - PHIEN BAN {__version__} ({RELEASE_DATE})", ""]
    notes = BEGINNER_HIGHLIGHTS + (ADVANCED_HIGHLIGHTS if advanced else ())
    for note in notes:
        lines.extend((f"  - {note}", ""))
    lines.extend(
        (
            "Xem day du: CHANGELOG.md",
            "",
            "Lam theo vi du: HUONG_DAN_SU_DUNG.md",
        )
    )
    return "\n".join(lines)
