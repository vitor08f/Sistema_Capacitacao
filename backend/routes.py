import logging
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from .business_calendar import is_business_day
from .database import get_db
from .emailer import send_notification
from .models import Agendamento, Bloqueio, Lead
from .schemas import AppointmentCreate, BlockCreate, LeadCreate, ManualAppointment, StatusUpdate
from .settings import settings

api = APIRouter(prefix="/api/v1")
admin = APIRouter(prefix="/api/v1/admin")
basic = HTTPBasic()
logger = logging.getLogger(__name__)
BUSINESS_TZ = ZoneInfo(settings.timezone)
SLOT_TIMES = [time(h) for h in (9, 10, 11, 14, 15, 16, 17)]
SLOT_LENGTH = timedelta(hours=1)


def require_admin(credentials: HTTPBasicCredentials = Depends(basic)):
    import secrets
    if not settings.admin_password or not (secrets.compare_digest(credentials.username, settings.admin_username) and secrets.compare_digest(credentials.password, settings.admin_password)):
        raise HTTPException(status_code=401, detail="Credenciais inválidas", headers={"WWW-Authenticate": "Basic"})
    return credentials.username


def local_slot(day: date, hour: time) -> tuple[datetime, datetime]:
    start = datetime.combine(day, hour, BUSINESS_TZ)
    return start.astimezone(timezone.utc), (start + SLOT_LENGTH).astimezone(timezone.utc)


def take_day_lock(db: Session, day: date) -> None:
    # SQLite has no advisory locks; reserve its write transaction before checking slots.
    if db.get_bind().dialect.name == "sqlite":
        db.execute(text("BEGIN IMMEDIATE"))
    else:
        db.execute(text("SELECT pg_advisory_xact_lock(hashtext(:lock_key))"), {"lock_key": f"agenda:{day.isoformat()}"})


def get_available(db: Session, day: date) -> list[str]:
    if not is_business_day(day):
        return []
    result = []
    now = datetime.now(timezone.utc)
    for hour in SLOT_TIMES:
        start, end = local_slot(day, hour)
        if start <= now:
            continue
        booked = db.scalar(select(Agendamento.id).where(Agendamento.status != "cancelado", Agendamento.inicio == start))
        blocked = db.scalar(select(Bloqueio.id).where(Bloqueio.inicio < end, (Bloqueio.fim.is_(None)) | (Bloqueio.fim > start)).limit(1))
        if not booked and not blocked:
            result.append(hour.strftime("%H:%M"))
    return result


@api.get("/disponibilidade")
def availability(data: date, db: Session = Depends(get_db)):
    if data < datetime.now(BUSINESS_TZ).date():
        raise HTTPException(422, "A data deve ser hoje ou futura.")
    return {"data": data.isoformat(), "fuso": settings.timezone, "horarios": get_available(db, data)}


@api.post("/leads", status_code=201)
def create_lead(payload: LeadCreate, db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    lead = Lead(nome=payload.nome, email=str(payload.email), telefone=payload.telefone, area_assunto=payload.area,
                formato="Remoto" if payload.formato == "Online" else "Presencial", mensagem=payload.mensagem,
                consentimento_lgpd=True, consentido_em=now, criado_em=now)
    db.add(lead)
    db.commit()
    db.refresh(lead)
    send_notification("Novo lead recebido", f"{lead.nome}, {lead.email}, {lead.telefone} — {lead.area_assunto}.")
    return {"id": lead.id, "status": "recebido"}


def create_booking(db: Session, payload: AppointmentCreate | None, lead: Lead | None, day: date, hour: time) -> Agendamento:
    if hour not in SLOT_TIMES:
        raise HTTPException(422, "Horário fora da agenda de atendimento.")
    if day < datetime.now(BUSINESS_TZ).date() or not is_business_day(day):
        raise HTTPException(422, "Escolha uma data futura em dia de expediente.")
    take_day_lock(db, day)
    if hour.strftime("%H:%M") not in get_available(db, day):
        raise HTTPException(status.HTTP_409_CONFLICT, "Este horário acabou de ser ocupado. Escolha outro horário disponível.")
    start, end = local_slot(day, hour)
    if lead is None and payload is not None:
        lead = Lead(nome=payload.nome, email=str(payload.email), telefone=payload.telefone, area_assunto=payload.area,
                    formato="Remoto" if payload.formato == "Online" else "Presencial", mensagem=payload.mensagem,
                    consentimento_lgpd=True, consentido_em=datetime.now(timezone.utc), criado_em=datetime.now(timezone.utc))
        db.add(lead)
        db.flush()
    appointment = Agendamento(lead_id=lead.id, inicio=start, fim=end, status="solicitado", criado_em=datetime.now(timezone.utc))
    db.add(appointment)
    try:
        db.commit()
        db.refresh(appointment)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Este horário acabou de ser ocupado. Escolha outro horário disponível.") from exc
    return appointment


@api.post("/agendamentos", status_code=201)
def create_appointment(payload: AppointmentCreate, db: Session = Depends(get_db)):
    appointment = create_booking(db, payload, None, payload.data, payload.hora)
    lead = db.get(Lead, appointment.lead_id)
    send_notification("Novo pedido de agendamento", f"Pedido de {lead.nome}, {lead.email}, {appointment.inicio.isoformat()} ({settings.timezone}).")
    send_notification("Recebemos seu pedido de agendamento", f"Olá, {lead.nome}. Seu pedido foi recebido e será confirmado pelo escritório.", str(lead.email))
    return {"id": appointment.id, "status": appointment.status, "inicio": appointment.inicio.isoformat(), "fuso": settings.timezone}


@admin.get("/agendamentos", dependencies=[Depends(require_admin)])
def list_appointments(db: Session = Depends(get_db)):
    rows = db.scalars(select(Agendamento).order_by(Agendamento.inicio.desc())).all()
    return [{"id": a.id, "lead_id": a.lead_id, "nome": a.lead.nome, "email": a.lead.email, "telefone": a.lead.telefone,
             "area": a.lead.area_assunto, "formato": a.lead.formato, "inicio": a.inicio.isoformat(), "status": a.status} for a in rows]


@admin.patch("/agendamentos/{appointment_id}", dependencies=[Depends(require_admin)])
def update_status(appointment_id: int, payload: StatusUpdate, db: Session = Depends(get_db)):
    appointment = db.get(Agendamento, appointment_id)
    if not appointment:
        raise HTTPException(404, "Agendamento não encontrado.")
    appointment.status = payload.status
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "Já existe outro agendamento ativo nesse horário.") from exc
    return {"id": appointment.id, "status": appointment.status}


@admin.post("/agendamentos", status_code=201, dependencies=[Depends(require_admin)])
def manual_appointment(payload: ManualAppointment, db: Session = Depends(get_db)):
    lead = db.get(Lead, payload.lead_id)
    if not lead:
        raise HTTPException(404, "Lead não encontrado.")
    appointment = create_booking(db, None, lead, payload.data, payload.hora)
    return {"id": appointment.id, "status": appointment.status, "inicio": appointment.inicio.isoformat()}


@admin.get("/leads", dependencies=[Depends(require_admin)])
def list_leads(db: Session = Depends(get_db)):
    rows = db.scalars(select(Lead).order_by(Lead.criado_em.desc())).all()
    return [{"id": lead.id, "nome": lead.nome, "email": lead.email, "telefone": lead.telefone, "area": lead.area_assunto, "criado_em": lead.criado_em.isoformat()} for lead in rows]


@admin.post("/bloqueios", status_code=201, dependencies=[Depends(require_admin)])
def create_block(payload: BlockCreate, db: Session = Depends(get_db)):
    take_day_lock(db, payload.data)
    if payload.hora_inicio is None:
        start = datetime.combine(payload.data, time.min, BUSINESS_TZ).astimezone(timezone.utc)
        end = datetime.combine(payload.data + timedelta(days=1), time.min, BUSINESS_TZ).astimezone(timezone.utc)
    else:
        start = datetime.combine(payload.data, payload.hora_inicio, BUSINESS_TZ).astimezone(timezone.utc)
        end = datetime.combine(payload.data, payload.hora_fim, BUSINESS_TZ).astimezone(timezone.utc)
    conflict = db.scalar(select(Agendamento.id).where(Agendamento.status != "cancelado", Agendamento.inicio < end, Agendamento.fim > start).limit(1))
    if conflict:
        db.rollback()
        raise HTTPException(409, "O intervalo contém agendamento ativo.")
    block = Bloqueio(inicio=start, fim=end, motivo=payload.motivo, criado_em=datetime.now(timezone.utc))
    db.add(block)
    db.commit()
    return {"id": block.id, "inicio": start.isoformat(), "fim": end.isoformat()}
