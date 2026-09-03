from datetime import date, timedelta
import secrets

from fastapi import APIRouter, HTTPException

from lib.dates import today_iso
from lib.db import db
from models.appointments import Appointment, AppointmentCreate, AvailableDate, BookingOptions


router = APIRouter(prefix="/appointments", tags=["appointments"])
AVAILABLE_WEEKDAYS = {1, 3, 5}  # Tuesday, Thursday, Saturday
AVAILABLE_DAY_NAMES = ["Tuesday", "Thursday", "Saturday"]


def validate_requested_date(value: str) -> None:
    try:
        requested = date.fromisoformat(value)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Please choose a valid consultation date.") from exc

    if requested.isoformat() < today_iso("Asia/Kolkata"):
        raise HTTPException(status_code=422, detail="Please choose a future consultation date.")
    if requested.weekday() not in AVAILABLE_WEEKDAYS:
        raise HTTPException(status_code=422, detail="Consultations are available by appointment on Tuesday, Thursday, or Saturday.")


@router.get("/options", response_model=BookingOptions)
async def get_booking_options() -> BookingOptions:
    current = date.fromisoformat(today_iso("Asia/Kolkata"))
    available_dates: list[AvailableDate] = []
    offset = 0
    while len(available_dates) < 9:
        candidate = current + timedelta(days=offset)
        if candidate.weekday() in AVAILABLE_WEEKDAYS:
            available_dates.append(
                AvailableDate(
                    date=candidate.isoformat(),
                    day_label=candidate.strftime("%A"),
                    display_label=candidate.strftime("%d %b"),
                )
            )
        offset += 1
    return BookingOptions(
        timezone="Asia/Kolkata",
        available_days=AVAILABLE_DAY_NAMES,
        available_dates=available_dates,
    )


@router.post("", response_model=Appointment, status_code=201)
async def create_appointment(payload: AppointmentCreate) -> Appointment:
    validate_requested_date(payload.preferred_date)
    appointment = Appointment(
        **payload.model_dump(),
        reference=f"AMY-{secrets.token_hex(3).upper()}",
    )
    await db.appointments.insert_one(appointment.model_dump())
    return appointment