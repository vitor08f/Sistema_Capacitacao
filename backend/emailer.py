import logging
import resend
from .settings import settings

logger = logging.getLogger(__name__)


def send_notification(subject: str, text: str, recipient: str | None = None) -> None:
    target = recipient or settings.notification_email
    if not settings.resend_api_key or not target:
        logger.info("E-mail não enviado: configure RESEND_API_KEY e NOTIFICATION_EMAIL.")
        return
    try:
        resend.api_key = settings.resend_api_key
        resend.Emails.send({"from": settings.email_from, "to": [target], "subject": subject, "text": text})
    except Exception:
        logger.exception("Falha ao enviar e-mail pelo Resend.")
