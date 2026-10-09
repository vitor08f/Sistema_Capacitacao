import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


@dataclass(frozen=True)
class Configuracoes:
    url_banco_dados: str = os.getenv("DATABASE_URL") or "sqlite:///./sql_app.db"
    fuso_horario: str = os.getenv("BUSINESS_TIMEZONE", "America/Sao_Paulo")
    feriados_empresa: str = os.getenv("BUSINESS_HOLIDAYS", "")
    usuario_administrador: str = os.getenv("ADMIN_USERNAME", "admin")
    senha_administrador: str = os.getenv("ADMIN_PASSWORD", "")
    chave_api_resend: str = os.getenv("RESEND_API_KEY", "")
    remetente_email: str = os.getenv("EMAIL_FROM", "Agenda <onboarding@resend.dev>")
    email_notificacao: str = os.getenv("NOTIFICATION_EMAIL", "")
    criar_tabelas: bool = os.getenv("CREATE_TABLES", "true").lower() == "true"


configuracoes = Configuracoes()
