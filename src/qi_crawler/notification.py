"""Notification module: email alerts and digest for procurement opportunities.

This module provides automated notification capabilities:
- Daily email digest with new matching packages
- Priority alerts for high-score opportunities
- Closing-soon reminders (T-7, T-3, T-1)
- KQLCNT alerts when tracked packages have results
- HTML email template with ranked table
"""

from __future__ import annotations

import logging
import smtplib
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from sqlalchemy import select

from .db import Database
from .models import BidResult, Notice
from .opportunity import OpportunityAssessment

logger = logging.getLogger(__name__)


@dataclass
class NotificationConfig:
    """Configuration for the notification system."""

    enabled: bool = False
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_use_tls: bool = True
    email_from: str | None = None
    email_to: list[str] = field(default_factory=list)
    send_daily_digest: bool = True
    send_priority_alerts: bool = True
    send_closing_alerts: bool = True
    closing_alert_days: list[int] = field(default_factory=lambda: [7, 3, 1])
    digest_hour: int = 8  # Send digest at 8am.


@dataclass(frozen=True)
class NotificationSummary:
    """Summary of notifications sent in one cycle."""

    total_sent: int = 0
    digest_sent: bool = False
    priority_alerts: int = 0
    closing_alerts: int = 0
    errors: list[str] = field(default_factory=list)


def _build_digest_html(
    assessments: list[tuple[Notice, OpportunityAssessment]],
    new_results: list[BidResult],
    date_str: str,
) -> str:
    """Build an HTML email body for the daily digest."""
    priority_rows = [
        (n, a) for n, a in assessments if a.status == "PRIORITY"
    ]
    review_rows = [
        (n, a) for n, a in assessments if a.status == "REVIEW"
    ]
    closing_soon = [
        (n, a) for n, a in assessments
        if a.days_left is not None and 0 < a.days_left <= 7
    ]

    rows_html = ""
    for notice, assessment in priority_rows + review_rows:
        color = "#27ae60" if assessment.status == "PRIORITY" else "#f39c12"
        alerts = " ".join(f"[{a}]" for a in assessment.alerts) if assessment.alerts else ""
        rows_html += f"""
        <tr>
            <td style="color:{color};font-weight:bold">{assessment.status}</td>
            <td>{assessment.score or '-'}</td>
            <td>{notice.notice_code or '-'}</td>
            <td>{(notice.title or '-')[:80]}</td>
            <td>{notice.buyer or '-'}</td>
            <td>{notice.closing_at or '-'}</td>
            <td>{f'{assessment.days_left:.0f}' if assessment.days_left is not None else '-'}</td>
            <td>{notice.location or '-'}</td>
            <td>{alerts}</td>
        </tr>"""

    results_html = ""
    if new_results:
        results_html = "<h3>Ket qua lua chon nha thau moi</h3><ul>"
        for r in new_results[:20]:
            results_html += (
                f"<li><strong>{r.notice_code or '-'}</strong>: "
                f"Nha thau trung: {r.contractor_name} - "
                f"Gia trung: {r.winning_price:,.0f} {r.currency or 'VND'}</li>"
                if r.winning_price
                else f"<li><strong>{r.notice_code or '-'}</strong>: {r.contractor_name}</li>"
            )
        results_html += "</ul>"

    return f"""
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; color: #2c3e50; }}
            h2 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 8px; }}
            h3 {{ color: #34495e; }}
            table {{ border-collapse: collapse; width: 100%; margin: 16px 0; }}
            th {{ background: #2c3e50; color: white; padding: 10px 8px; text-align: left; }}
            td {{ padding: 8px; border-bottom: 1px solid #ecf0f1; }}
            tr:hover {{ background: #f8f9fa; }}
            .summary {{ background: #ecf0f1; padding: 16px; border-radius: 8px; margin: 16px 0; }}
            .stat {{ display: inline-block; margin-right: 24px; }}
            .stat-value {{ font-size: 24px; font-weight: bold; color: #3498db; }}
            .footer {{ color: #95a5a6; font-size: 12px; margin-top: 24px; }}
        </style>
    </head>
    <body>
        <h2>QI-Crawler Bao Cao Hang Ngay — {date_str}</h2>

        <div class="summary">
            <span class="stat">
                <span class="stat-value">{len(priority_rows)}</span> PRIORITY
            </span>
            <span class="stat">
                <span class="stat-value">{len(review_rows)}</span> REVIEW
            </span>
            <span class="stat">
                <span class="stat-value">{len(closing_soon)}</span> Sap dong thau
            </span>
            <span class="stat">
                <span class="stat-value">{len(new_results)}</span> KQLCNT moi
            </span>
        </div>

        <h3>Co hoi uu tien</h3>
        <table>
            <thead>
                <tr>
                    <th>Trang thai</th>
                    <th>Diem</th>
                    <th>Ma TBMT</th>
                    <th>Ten goi thau</th>
                    <th>Ben moi thau</th>
                    <th>Dong thau</th>
                    <th>Con (ngay)</th>
                    <th>Dia diem</th>
                    <th>Canh bao</th>
                </tr>
            </thead>
            <tbody>
                {rows_html or '<tr><td colspan="9" style="text-align:center">Khong co co hoi moi</td></tr>'}
            </tbody>
        </table>

        {results_html}

        <p class="footer">
            Bao cao tu dong boi QI-Crawler. Vui long kiem tra tren he thong truoc khi hanh dong.<br>
            Khong phai xac suat trung thau. Lien he nguoi van hanh de dieu chinh bo loc.
        </p>
    </body>
    </html>
    """


def send_email(
    config: NotificationConfig,
    subject: str,
    html_body: str,
) -> bool:
    """Send an HTML email using SMTP configuration."""
    if not config.smtp_host or not config.email_from or not config.email_to:
        logger.warning("Cau hinh SMTP chua day du, khong gui duoc email.")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = config.email_from
    msg["To"] = ", ".join(config.email_to)
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        if config.smtp_use_tls:
            server = smtplib.SMTP(config.smtp_host, config.smtp_port)
            server.ehlo()
            server.starttls()
        else:
            server = smtplib.SMTP(config.smtp_host, config.smtp_port)

        if config.smtp_username and config.smtp_password:
            server.login(config.smtp_username, config.smtp_password)

        server.sendmail(config.email_from, config.email_to, msg.as_string())
        server.quit()
        logger.info("Da gui email toi %s", config.email_to)
        return True
    except (OSError, smtplib.SMTPException) as exc:
        logger.error("Loi gui email: %s", exc)
        return False


def send_daily_digest(
    config: NotificationConfig,
    assessments: list[tuple[Notice, OpportunityAssessment]],
    db: Database,
) -> NotificationSummary:
    """Compile and send the daily digest email."""
    errors: list[str] = []
    date_str = datetime.now(UTC).strftime("%Y-%m-%d")

    # Find recent KQLCNT results (last 24h).
    new_results: list[BidResult] = []
    with db.session() as session:
        cutoff = datetime.now(UTC) - timedelta(hours=24)
        new_results = list(
            session.scalars(
                select(BidResult)
                .where(BidResult.created_at >= cutoff)
                .order_by(BidResult.created_at.desc())
                .limit(50)
            ).all()
        )
        session.expunge_all()

    html = _build_digest_html(assessments, new_results, date_str)
    priority_count = sum(1 for _, a in assessments if a.status == "PRIORITY")
    subject = f"QI-Crawler: {priority_count} co hoi uu tien — {date_str}"

    sent = send_email(config, subject, html)
    if not sent:
        errors.append("Khong gui duoc email digest")

    return NotificationSummary(
        total_sent=1 if sent else 0,
        digest_sent=sent,
        priority_alerts=priority_count,
        closing_alerts=sum(
            1 for _, a in assessments
            if a.days_left is not None and 0 < a.days_left <= 7
        ),
        errors=errors,
    )


def send_priority_alert(
    config: NotificationConfig,
    notice: Notice,
    assessment: OpportunityAssessment,
) -> bool:
    """Send immediate alert for a new PRIORITY opportunity."""
    if not config.send_priority_alerts:
        return False

    subject = f"[PRIORITY] Co hoi moi: {notice.notice_code or notice.title or 'N/A'}"
    html = f"""
    <html><body style="font-family: Arial, sans-serif;">
    <h2 style="color: #27ae60;">Co hoi uu tien moi!</h2>
    <table style="border-collapse: collapse;">
        <tr><td style="padding:4px 12px;font-weight:bold">Ma TBMT:</td>
            <td>{notice.notice_code or '-'}</td></tr>
        <tr><td style="padding:4px 12px;font-weight:bold">Ten goi:</td>
            <td>{notice.title or '-'}</td></tr>
        <tr><td style="padding:4px 12px;font-weight:bold">Ben moi thau:</td>
            <td>{notice.buyer or '-'}</td></tr>
        <tr><td style="padding:4px 12px;font-weight:bold">Gia goi thau:</td>
            <td>{notice.package_price:,.0f} {notice.currency or 'VND'}</td></tr>
        <tr><td style="padding:4px 12px;font-weight:bold">Dong thau:</td>
            <td>{notice.closing_at or '-'}</td></tr>
        <tr><td style="padding:4px 12px;font-weight:bold">Dia diem:</td>
            <td>{notice.location or '-'}</td></tr>
        <tr><td style="padding:4px 12px;font-weight:bold">Diem:</td>
            <td style="font-size:18px;color:#27ae60;font-weight:bold">
                {assessment.score or '-'}/100</td></tr>
        <tr><td style="padding:4px 12px;font-weight:bold">Hanh dong:</td>
            <td>{assessment.next_action}</td></tr>
    </table>
    <p><a href="{notice.source_url}">Xem chi tiet tren nguon goc</a></p>
    </body></html>
    """
    return send_email(config, subject, html)


def send_closing_alert(
    config: NotificationConfig,
    notice: Notice,
    days_left: float,
) -> bool:
    """Send alert for a package approaching its closing deadline."""
    if not config.send_closing_alerts:
        return False

    urgency = "KHAN CAP" if days_left <= 1 else "SAP HET HAN"
    subject = f"[{urgency}] Goi thau con {days_left:.0f} ngay: {notice.notice_code or 'N/A'}"
    html = f"""
    <html><body style="font-family: Arial, sans-serif;">
    <h2 style="color: #e74c3c;">Goi thau sap het han!</h2>
    <p style="font-size:18px">Con <strong>{days_left:.0f} ngay</strong> de nop ho so.</p>
    <table style="border-collapse: collapse;">
        <tr><td style="padding:4px 12px;font-weight:bold">Ma TBMT:</td>
            <td>{notice.notice_code or '-'}</td></tr>
        <tr><td style="padding:4px 12px;font-weight:bold">Ten goi:</td>
            <td>{notice.title or '-'}</td></tr>
        <tr><td style="padding:4px 12px;font-weight:bold">Dong thau:</td>
            <td style="color:#e74c3c;font-weight:bold">{notice.closing_at or '-'}</td></tr>
        <tr><td style="padding:4px 12px;font-weight:bold">Dia diem:</td>
            <td>{notice.location or '-'}</td></tr>
    </table>
    <p><a href="{notice.source_url}">Xem chi tiet</a></p>
    </body></html>
    """
    return send_email(config, subject, html)
