import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from utils import format_price, today_str

logger = logging.getLogger(__name__)


def build_price_email(
    game_name: str,
    store: str,
    current_price: Optional[float],
    previous_price: Optional[float],
    price_diff: Optional[float],
    lowest_price: Optional[float],
    lowest_currency: str,
    target_price: Optional[float],
    target_currency: Optional[str],
    cover_image: str,
    currency: str = "INR",
    is_new_low: bool = False,
) -> str:
    price_str = format_price(current_price, currency)
    prev_str = format_price(previous_price, currency)
    lowest_str = format_price(lowest_price, lowest_currency)
    target_str = (
        format_price(target_price, target_currency)
        if target_price is not None and target_currency
        else "Not set"
    )

    if price_diff is not None:
        diff_str = format_price(abs(price_diff), currency)
        if price_diff < 0:
            change_html = f'<span style="color:#22c55e">\u25bc Down by {diff_str}</span>'
        else:
            change_html = f'<span style="color:#ef4444">\u25b2 Up by {diff_str}</span>'
    else:
        change_html = '<span style="color:#6b7280">No change</span>'

    reached_target = ""
    if (
        target_price is not None
        and current_price is not None
        and target_currency
        and currency == target_currency
        and current_price <= target_price
    ):
        reached_target = (
            '<p style="color:#22c55e; font-weight:bold; font-size:18px;">'
            "\u2705 Target price reached!</p>"
        )

    new_low = ""
    if is_new_low:
        new_low = (
            '<p style="color:#f59e0b; font-weight:bold; font-size:16px;">'
            "\ud83c\udf1f New all-time low!</p>"
        )

    cover_html = ""
    if cover_image:
        cover_html = (
            f'<img src="{cover_image}" alt="{game_name}" '
            f'style="width:100%; max-width:460px; border-radius:12px; margin-bottom:16px;">'
        )

    store_logo = ""
    store_lower = store.lower()
    if "steam" in store_lower:
        store_logo = (
            '<span style="display:inline-block; background:#1b2838; color:#66c0f4; '
            'padding:4px 14px; border-radius:20px; font-size:12px; font-weight:600;">STEAM</span>'
        )
    elif "epic" in store_lower:
        store_logo = (
            '<span style="display:inline-block; background:#121212; color:#ffffff; '
            'padding:4px 14px; border-radius:20px; font-size:12px; font-weight:600;">EPIC GAMES</span>'
        )
    elif "gog" in store_lower:
        store_logo = (
            '<span style="display:inline-block; background:#2b2b2b; color:#d2b48c; '
            'padding:4px 14px; border-radius:20px; font-size:12px; font-weight:600;">GOG</span>'
        )

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0; padding:0; background-color:#0b1120; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#0b1120; padding:24px;">
<tr><td align="center">
<table width="540" cellpadding="0" cellspacing="0" style="background:linear-gradient(145deg,#1a2332,#0f172a); border-radius:18px; padding:28px; border:1px solid rgba(59,130,246,0.15); box-shadow:0 8px 32px rgba(0,0,0,0.4);">
<tr><td style="text-align:center;">
{cover_html}
{store_logo}
<h1 style="color:#f1f5f9; font-size:24px; margin:12px 0 4px 0; font-weight:700;">{game_name}</h1>
<p style="color:#64748b; font-size:13px; margin:0 0 20px 0;">{today_str()}</p>
{reached_target}
{new_low}
<table width="100%" cellpadding="10" cellspacing="0" style="margin:16px 0; background:rgba(15,23,42,0.6); border-radius:12px;">
<tr><td style="color:#94a3b8; font-size:14px; border-bottom:1px solid rgba(51,65,85,0.5);">Current Price</td><td style="text-align:right; color:#f1f5f9; font-size:22px; font-weight:700; border-bottom:1px solid rgba(51,65,85,0.5);">{price_str}</td></tr>
<tr><td style="color:#94a3b8; font-size:14px; border-bottom:1px solid rgba(51,65,85,0.5);">Previous Price</td><td style="text-align:right; color:#94a3b8; font-size:16px; border-bottom:1px solid rgba(51,65,85,0.5);">{prev_str}</td></tr>
<tr><td style="color:#94a3b8; font-size:14px; border-bottom:1px solid rgba(51,65,85,0.5);">Change</td><td style="text-align:right; font-size:16px; font-weight:600; border-bottom:1px solid rgba(51,65,85,0.5);">{change_html}</td></tr>
<tr><td style="color:#94a3b8; font-size:14px; border-bottom:1px solid rgba(51,65,85,0.5);">Lowest Ever</td><td style="text-align:right; color:#22c55e; font-size:16px; font-weight:600; border-bottom:1px solid rgba(51,65,85,0.5);">{lowest_str}</td></tr>
<tr><td style="color:#94a3b8; font-size:14px;">Target Price</td><td style="text-align:right; color:#f1f5f9; font-size:16px;">{target_str}</td></tr>
</table>
<p style="color:#475569; font-size:11px; margin:20px 0 0 0; letter-spacing:0.5px;">GAME PRICE TRACKER &middot; AUTOMATED PRICE ALERT</p>
</td></tr></table>
</td></tr></table>
</body>
</html>"""
    return html


def build_summary_email(changed: list[dict], unchanged_count: int) -> str:
    items_html = ""
    for item in changed:
        direction = "\u25bc" if item.get("diff", 0) < 0 else "\u25b2"
        color = "#22c55e" if item["diff"] < 0 else "#ef4444"
        items_html += f"""
        <tr>
            <td style="padding:10px 8px; border-bottom:1px solid rgba(51,65,85,0.4); color:#f1f5f9; font-size:14px;">{item['name']}</td>
            <td style="padding:10px 8px; border-bottom:1px solid rgba(51,65,85,0.4); color:#94a3b8; text-align:center; font-size:12px;">{item['store'].upper()}</td>
            <td style="padding:10px 8px; border-bottom:1px solid rgba(51,65,85,0.4); color:#f1f5f9; text-align:right; font-size:14px; font-weight:600;">{item['price']}</td>
            <td style="padding:10px 8px; border-bottom:1px solid rgba(51,65,85,0.4); color:{color}; text-align:right; font-size:13px; font-weight:700;">{direction} {item['diff_str']}</td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0; padding:0; background-color:#0b1120; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#0b1120; padding:24px;">
<tr><td align="center">
<table width="540" cellpadding="0" cellspacing="0" style="background:linear-gradient(145deg,#1a2332,#0f172a); border-radius:18px; padding:28px; border:1px solid rgba(59,130,246,0.15); box-shadow:0 8px 32px rgba(0,0,0,0.4);">
<tr><td style="text-align:center;">
<div style="font-size:40px; margin-bottom:8px;">\ud83d\udcc8</div>
<h1 style="color:#f1f5f9; font-size:22px; margin:0 0 4px 0; font-weight:700;">Daily Price Summary</h1>
<p style="color:#64748b; font-size:13px; margin:0 0 24px 0;">{today_str()}</p>
<table width="100%" cellpadding="0" cellspacing="0" style="background:rgba(15,23,42,0.6); border-radius:12px; overflow:hidden;">
<tr style="color:#64748b; font-size:11px; text-transform:uppercase; letter-spacing:0.5px;">
<th style="text-align:left; padding:12px 8px 8px; border-bottom:1px solid rgba(51,65,85,0.4);">Game</th>
<th style="text-align:center; padding:12px 8px 8px; border-bottom:1px solid rgba(51,65,85,0.4);">Store</th>
<th style="text-align:right; padding:12px 8px 8px; border-bottom:1px solid rgba(51,65,85,0.4);">Price</th>
<th style="text-align:right; padding:12px 8px 8px; border-bottom:1px solid rgba(51,65,85,0.4);">Change</th>
</tr>
{items_html}
</table>
<p style="color:#64748b; font-size:14px; margin-top:20px;">{unchanged_count} game(s) unchanged.</p>
<p style="color:#475569; font-size:11px; margin:16px 0 0 0; letter-spacing:0.5px;">GAME PRICE TRACKER</p>
</td></tr></table>
</td></tr></table>
</body>
</html>"""
    return html


def send_email(
    smtp_server: str,
    smtp_port: int,
    email_address: str,
    email_password: str,
    to_address: str,
    subject: str,
    html_body: str,
) -> bool:
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = email_address
        msg["To"] = to_address
        msg["Subject"] = subject
        msg.attach(MIMEText(html_body, "html"))
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(email_address, email_password)
            server.send_message(msg)
        logger.info("Email sent to %s: %s", to_address, subject)
        return True
    except smtplib.SMTPException as e:
        logger.error("Failed to send email: %s", e)
        return False
    except Exception as e:
        logger.error("Email error: %s", e)
        return False


def send_price_alert(
    email_address: str,
    email_password: str,
    to_address: str,
    game_name: str,
    store: str,
    current_price: Optional[float],
    previous_price: Optional[float],
    price_diff: Optional[float],
    lowest_price: Optional[float],
    lowest_currency: str,
    target_price: Optional[float],
    target_currency: Optional[str],
    cover_image: str,
    currency: str = "INR",
    is_new_low: bool = False,
    smtp_server: str = "smtp.gmail.com",
    smtp_port: int = 587,
) -> bool:
    price_display = format_price(current_price, currency)
    subject = f"\ud83d\udcc8 Price Alert: {game_name} - {price_display}"
    html = build_price_email(
        game_name, store, current_price, previous_price, price_diff,
        lowest_price, lowest_currency, target_price, target_currency,
        cover_image, currency, is_new_low,
    )
    return send_email(
        smtp_server, smtp_port, email_address, email_password,
        to_address, subject, html,
    )


def send_summary_email(
    email_address: str,
    email_password: str,
    to_address: str,
    changed: list[dict],
    unchanged_count: int,
    smtp_server: str = "smtp.gmail.com",
    smtp_port: int = 587,
) -> bool:
    subject = f"\ud83d\udcc8 Daily Price Summary - {today_str()}"
    html = build_summary_email(changed, unchanged_count)
    return send_email(
        smtp_server, smtp_port, email_address, email_password,
        to_address, subject, html,
    )


def send_daily_report(
    email_address: str,
    email_password: str,
    to_address: str,
    games: list[dict],
    history: dict,
    smtp_server: str = "smtp.gmail.com",
    smtp_port: int = 587,
) -> bool:
    from report import build_daily_report
    date = today_str()
    subject = f"\ud83c\udfae Daily Game Price Report \u2014 {date}"
    html = build_daily_report(games, history)
    return send_email(
        smtp_server, smtp_port, email_address, email_password,
        to_address, subject, html,
    )
