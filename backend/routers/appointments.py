from datetime import date
import secrets

from fastapi import APIRouter, HTTPException

from lib.dates import today_iso
from lib.db import db
from models.appointments import Appointment, AppointmentCreate


router = APIRouter(prefix="/appointments", tags=["appointments"])
AVAILABLE_WEEKDAYS = {1, 3, 5}  # Tuesday, Thursday, Saturday


def validate_requested_date(value: str) -> None:
    try:
        requested = date.fromisoformat(value)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Please choose a valid consultation date.") from exc

    if requested.isoformat() < today_iso("Asia/Kolkata"):
        raise HTTPException(status_code=422, detail="Please choose a future consultation date.")
    if requested.weekday() not in AVAILABLE_WEEKDAYS:
        raise HTTPException(status_code=422, detail="Consultations are available by appointment on Tuesday, Thursday, or Saturday.")


@router.post("", response_model=Appointment, status_code=201)
async def create_appointment(payload: AppointmentCreate) -> Appointment:
    validate_requested_date(payload.preferred_date)
    appointment = Appointment(
        **payload.model_dump(),
        reference=f"AMY-{secrets.token_hex(3).upper()}",
    )
    await db.appointments.insert_one(appointment.model_dump())
    return appointment