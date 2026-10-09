import re
from datetime import date, time
from typing import Literal
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


def clean_text(value: str) -> str:
    value = re.sub(r"<[^>]*>", "", value)
    return "".join(ch for ch in value if ch.isprintable()).strip()


class LeadCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    nome: str = Field(min_length=3, max_length=120)
    email: EmailStr
    telefone: str = Field(min_length=10, max_length=30)
    area: Literal["Direito civil", "Família e sucessões", "Trabalhista", "Empresarial", "Previdenciário", "Consumidor", "Outro"]
    formato: Literal["Presencial", "Online"]
    mensagem: str | None = Field(default=None, max_length=800)
    consentimento_lgpd: Literal[True]

    @field_validator("nome", "telefone", "mensagem", mode="before")
    @classmethod
    def sanitize(cls, value):
        return clean_text(value) if isinstance(value, str) else value

    @field_validator("nome")
    @classmethod
    def require_full_name(cls, value: str) -> str:
        if len(value.split()) < 2:
            raise ValueError("Informe nome e sobrenome.")
        return value

    @field_validator("telefone")
    @classmethod
    def valid_phone(cls, value: str) -> str:
        digits = re.sub(r"\D", "", value)
        if len(digits) not in (10, 11):
            raise ValueError("Informe um telefone com DDD e 10 ou 11 dígitos.")
        return digits


class AppointmentCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    nome: str = Field(min_length=3, max_length=120)
    email: EmailStr
    telefone: str = Field(min_length=10, max_length=30)
    area: Literal["Direito civil", "Família e sucessões", "Trabalhista", "Empresarial", "Previdenciário", "Consumidor", "Outro"]
    formato: Literal["Presencial", "Online"]
    data: date
    hora: time
    mensagem: str | None = Field(default=None, max_length=800)
    consentimento_lgpd: Literal[True]

    @field_validator("nome", "telefone", "mensagem", mode="before")
    @classmethod
    def sanitize(cls, value):
        return clean_text(value) if isinstance(value, str) else value

    @field_validator("nome")
    @classmethod
    def require_full_name(cls, value: str) -> str:
        if len(value.split()) < 2:
            raise ValueError("Informe nome e sobrenome.")
        return value

    @field_validator("telefone")
    @classmethod
    def valid_phone(cls, value: str) -> str:
        digits = re.sub(r"\D", "", value)
        if len(digits) not in (10, 11):
            raise ValueError("Informe um telefone com DDD e 10 ou 11 dígitos.")
        return digits


class StatusUpdate(BaseModel):
    status: Literal["solicitado", "aprovado", "cancelado"]


class ManualAppointment(BaseModel):
    lead_id: int = Field(gt=0)
    data: date
    hora: time


class BlockCreate(BaseModel):
    data: date
    hora_inicio: time | None = None
    hora_fim: time | None = None
    motivo: str = Field(min_length=2, max_length=120)

    @field_validator("motivo", mode="before")
    @classmethod
    def sanitize_reason(cls, value):
        return clean_text(value) if isinstance(value, str) else value

    @field_validator("hora_fim")
    @classmethod
    def valid_interval(cls, value, info):
        start = info.data.get("hora_inicio")
        if (value is None) != (start is None):
            raise ValueError("Informe início e fim, ou deixe ambos vazios para bloquear o dia todo.")
        if start and value <= start:
            raise ValueError("O fim do bloqueio deve ser posterior ao início.")
        return value
