import logging
from zoneinfo import ZoneInfo
import resend
from .settings import configuracoes

logger = logging.getLogger(__name__)


def send_notification(subject: str, text: str, recipient: str | None = None) -> None:
    target = recipient or configuracoes.email_notificacao
    if not configuracoes.chave_api_resend or not target:
        logger.info("E-mail não enviado: configure RESEND_API_KEY e EMAIL_NOTIFICACAO.")
        return
    try:
        resend.api_key = configuracoes.chave_api_resend
        resend.Emails.send({"from": configuracoes.remetente_email, "to": [target], "subject": subject, "text": text})
    except Exception:
        logger.exception("Falha ao enviar e-mail pelo Resend.")
BUSINESS_TZ = ZoneInfo(configuracoes.fuso_horario)