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
    target_price: Optional[float],
    cover_image: str,
    currency: str = "USD",
    is_new_low: bool = False,
) -> str:
    price_str = format_price(current_price, currency)
    prev_str = format_price(previous_price, currency)
    lowest_str = format_price(lowest_price, currency)
    target_str = format_price(target_price, currency) if target_price is not None else "Not set"

    if price_diff is not None:
        diff_abs = abs(price_diff)
        diff_str = format_price(diff_abs, currency)
        if price_diff < 0:
            change_html = f'<span style="color:#22c55e">\u25bc Down by {diff_str}</span>'
        else:
            change_html = f'<span style="color:#ef4444">\u25b2 Up by {diff_str}</span>'
    else:
        change_html = '<span style="color:#6b7280">No change</span>'

    reached_target = ""
    if target_price is not None and current_price is not None and current_price <= target_price:
        reached_target = '<p style="color:#22c55e; font-weight:bold; font-size:18px;">\u2705 Target price reached!</p>'

    new_low = ""
    if is_new_low:
        new_low = '<p style="color:#f59e0b; font-weight:bold; font-size:16px;">\ud83c\udf1f New all-time low!</p>'

    cover_html = ""
    if cover_image:
        cover_html = f'<img src="{cover_image}" alt="{game_name}" style="width:100%; max-width:460px; border-radius:12px; margin-bottom:16px;">'

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0; padding:0; background-color:#0f172a; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background-color:#0f172a; padding:20px;">
<tr><td align="center">
<table width="520" cellpadding="0" cellspacing="0" style="background-color:#1e293b; border-radius:16px; padding:24px; border:1px solid #334155;">
<tr><td style="text-align:center;">
{cover_html}
<h1 style="color:#f1f5f9; font-size:22px; margin:0 0 8px 0;">{game_name}</h1>
<p style="color:#94a3b8; font-size:14px; margin:0 0 20px 0;">{store} &middot; {today_str()}</p>
{reached_target}
{new_low}
<table width="100%" cellpadding="8" cellspacing="0" style="margin-bottom:16px;">
<tr><td style="color:#94a3b8; font-size:14px;">Current Price</td><td style="text-align:right; color:#f1f5f9; font-size:18px; font-weight:bold;">{price_str}</td></tr>
<tr><td style="color:#94a3b8; font-size:14px;">Previous Price</td><td style="text-align:right; color:#f1f5f9; font-size:16px;">{prev_str}</td></tr>
<tr><td style="color:#94a3b8; font-size:14px;">Change</td><td style="text-align:right; font-size:16px; font-weight:bold;">{change_html}</td></tr>
<tr><td style="color:#94a3b8; font-size:14px;">Lowest Ever</td><td style="text-align:right; color:#22c55e; font-size:16px; font-weight:bold;">{lowest_str}</td></tr>
<tr><td style="color:#94a3b8; font-size:14px;">Target Price</td><td style="text-align:right; color:#f1f5f9; font-size:16px;">{target_str}</td></tr>
</table>
<p style="color:#64748b; font-size:12px; margin:0;">Game Price Tracker &middot; Automated Price Alert</p>
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
            <td style="padding:8px 0; border-bottom:1px solid #334155; color:#f1f5f9;">{item['name']}</td>
            <td style="padding:8px 0; border-bottom:1px solid #334155; color:#94a3b8; text-align:center;">{item['store']}</td>
            <td style="padding:8px 0; border-bottom:1px solid #334155; color:#f1f5f9; text-align:right;">{item['price']}</td>
            <td style="padding:8px 0; border-bottom:1px solid #334155; color:{color}; text-align:right; font-weight:bold;">{direction} {item['diff_str']}</td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0; padding:0; background-color:#0f172a; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background-color:#0f172a; padding:20px;">
<tr><td align="center">
<table width="520" cellpadding="0" cellspacing="0" style="background-color:#1e293b; border-radius:16px; padding:24px; border:1px solid #334155;">
<tr><td style="text-align:center;">
<h1 style="color:#f1f5f9; font-size:20px; margin:0 0 4px 0;">\ud83d\udcc8 Daily Price Summary</h1>
<p style="color:#94a3b8; font-size:14px; margin:0 0 20px 0;">{today_str()}</p>
<table width="100%" cellpadding="0" cellspacing="0">
<tr style="color:#64748b; font-size:12px; text-transform:uppercase;">
<th style="text-align:left; padding-bottom:8px; border-bottom:1px solid #334155;">Game</th>
<th style="text-align:center; padding-bottom:8px; border-bottom:1px solid #334155;">Store</th>
<th style="text-align:right; padding-bottom:8px; border-bottom:1px solid #334155;">Price</th>
<th style="text-align:right; padding-bottom:8px; border-bottom:1px solid #334155;">Change</th>
</tr>
{items_html}
</table>
<p style="color:#64748b; font-size:14px; margin-top:16px;">{unchanged_count} game(s) unchanged.</p>
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
    target_price: Optional[float],
    cover_image: str,
    currency: str = "USD",
    is_new_low: bool = False,
) -> bool:
    subject = f"\ud83d\udcc8 Price Alert: {game_name} - {format_price(current_price, currency)}"
    html = build_price_email(
        game_name, store, current_price, previous_price, price_diff,
        lowest_price, target_price, cover_image, currency, is_new_low,
    )
    return send_email(
        "smtp.gmail.com", 587, email_address, email_password,
        to_address, subject, html,
    )


def send_summary_email(
    email_address: str,
    email_password: str,
    to_address: str,
    changed: list[dict],
    unchanged_count: int,
) -> bool:
    subject = f"\ud83d\udcc8 Daily Price Summary - {today_str()}"
    html = build_summary_email(changed, unchanged_count)
    return send_email(
        "smtp.gmail.com", 587, email_address, email_password,
        to_address, subject, html,
    )
