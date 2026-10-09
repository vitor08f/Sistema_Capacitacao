from datetime import datetime, timezone
from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, String, Text, text
from sqlalchemy.types import TypeDecorator
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base


class UTCDateTime(TypeDecorator):
    """Store instants in UTC; restore aware UTC datetimes on SQLite reads."""
    impl = DateTime
    cache_ok = True

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(DateTime(timezone=dialect.name != "sqlite"))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        value = value.astimezone(timezone.utc)
        return value.replace(tzinfo=None) if dialect.name == "sqlite" else value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class Lead(Base):
    __tablename__ = "leads"
    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(254), nullable=False)
    telefone: Mapped[str] = mapped_column(String(30), nullable=False)
    area_assunto: Mapped[str] = mapped_column(String(40), nullable=False)
    formato: Mapped[str] = mapped_column(String(20), nullable=False)
    mensagem: Mapped[str | None] = mapped_column(Text)
    consentimento_lgpd: Mapped[bool] = mapped_column(Boolean, nullable=False)
    consentido_em: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    criado_em: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    agendamentos: Mapped[list["Agendamento"]] = relationship(back_populates="lead")


class Agendamento(Base):
    __tablename__ = "agendamentos"
    __table_args__ = (
        CheckConstraint("status IN ('solicitado', 'aprovado', 'cancelado')", name="ck_agendamentos_status"),
        Index("ix_agendamentos_lead_id", "lead_id"),
        Index("uq_agendamentos_inicio_ativo", "inicio", unique=True,
              postgresql_where=text("status <> 'cancelado'"), sqlite_where=text("status <> 'cancelado'")),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id", ondelete="RESTRICT"), nullable=False)
    inicio: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    fim: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="solicitado")
    criado_em: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    lead: Mapped[Lead] = relationship(back_populates="agendamentos")


class Bloqueio(Base):
    __tablename__ = "bloqueios"
    __table_args__ = (CheckConstraint("fim IS NULL OR fim > inicio", name="ck_bloqueios_intervalo"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    inicio: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    fim: Mapped[datetime | None] = mapped_column(UTCDateTime())
    motivo: Mapped[str] = mapped_column(String(120), nullable=False)
    criado_em: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
