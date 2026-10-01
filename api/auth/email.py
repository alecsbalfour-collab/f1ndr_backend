# api/auth/email.py
"""Outbound email over SMTP (stdlib), sent off the event loop."""

import asyncio
import logging
import smtplib
from email.message import EmailMessage

from api.config.settings_config import get_settings

logger = logging.getLogger(__name__)


def _send_smtp(message: EmailMessage) -> None:
    settings = get_settings()
    smtp_class = smtplib.SMTP_SSL if settings.SMTP_SSL else smtplib.SMTP
    with smtp_class(settings.SMTP_HOST, settings.SMTP_PORT, timeout=settings.SMTP_TIMEOUT_SECONDS) as smtp:
        if settings.SMTP_STARTTLS and not settings.SMTP_SSL:
            smtp.starttls()
        if settings.SMTP_USERNAME:
            smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD or "")
        smtp.send_message(message)


async def send_email(to: str, subject: str, body: str) -> bool:
    """Send a plain-text email. Returns False (and logs) instead of raising."""
    settings = get_settings()
    if not settings.SMTP_HOST:
        if settings.ENVIRONMENT == "production":
            logger.error("SMTP_HOST not configured; email '%s' to %s not sent", subject, to)
        else:
            logger.warning("SMTP_HOST not configured; would send '%s' to %s:\n%s", subject, to, body)
        return False
    message = EmailMessage()
    message["From"] = settings.EMAIL_FROM
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)
    try:
        await asyncio.to_thread(_send_smtp, message)
    except (smtplib.SMTPException, OSError):
        logger.exception("Failed to send email '%s' to %s", subject, to)
        return False
    return True
