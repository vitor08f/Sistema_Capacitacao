import logging

import resend

from .settings import configuracoes

registrador = logging.getLogger(__name__)


def enviar_notificacao(assunto: str, conteudo: str, destinatario: str | None = None) -> None:
    endereco_destinatario = destinatario or configuracoes.email_notificacao
    if not configuracoes.chave_api_resend or not endereco_destinatario:
        registrador.info("E-mail não enviado: configure RESEND_API_KEY e NOTIFICATION_EMAIL.")
        return
    try:
        resend.api_key = configuracoes.chave_api_resend
        resend.Emails.send({
            "from": configuracoes.remetente_email,
            "to": [endereco_destinatario],
            "subject": assunto,
            "text": conteudo,
        })
    except Exception:
        registrador.exception("Falha ao enviar e-mail pelo Resend.")
