from datetime import date, datetime, timedelta, timezone
import os
import secrets

from bson import ObjectId
from fastapi import APIRouter, File, HTTPException, UploadFile

from lib.dates import today_iso
from lib.db import db
from models.appointments import Appointment, AppointmentAttachment, AppointmentCreate, AvailableDate, BookingOptions


router = APIRouter(prefix="/appointments", tags=["appointments"])
AVAILABLE_WEEKDAYS = {1, 3, 5}  # Tuesday, Thursday, Saturday
AVAILABLE_DAY_NAMES = ["Tuesday", "Thursday", "Saturday"]
AVAILABLE_TIMES = [
    "10:00 AM", "11:00 AM", "12:00 PM", "1:00 PM", "2:00 PM",
    "3:00 PM", "4:00 PM", "5:00 PM", "6:00 PM",
]
LEGACY_TIME_PREFERENCES = {"Morning preference", "Afternoon preference", "Evening preference"}
ALLOWED_ATTACHMENT_TYPES = {"application/pdf", "image/jpeg", "image/png"}
MAX_ATTACHMENT_BYTES = 10 * 1024 * 1024


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
    while len(available_dates) < 18:
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
        available_times=AVAILABLE_TIMES,
        google_meet_enabled=(
            os.environ.get("GOOGLE_MEET_ENABLED", "false").lower() == "true"
            and bool(os.environ.get("GOOGLE_CLIENT_ID"))
            and bool(os.environ.get("GOOGLE_CLIENT_SECRET"))
        ),
    )


@router.post("/attachments", response_model=AppointmentAttachment, status_code=201)
async def upload_appointment_attachment(file: UploadFile = File(...)) -> AppointmentAttachment:
    if file.content_type not in ALLOWED_ATTACHMENT_TYPES:
        raise HTTPException(status_code=422, detail="Only PDF, JPG, and PNG files are supported.")
    content = await file.read(MAX_ATTACHMENT_BYTES + 1)
    await file.close()
    if len(content) > MAX_ATTACHMENT_BYTES:
        raise HTTPException(status_code=413, detail="Each attachment must be 10 MB or smaller.")
    if not content:
        raise HTTPException(status_code=422, detail="The selected attachment is empty.")

    document = {
        "file_name": file.filename or "attachment",
        "content_type": file.content_type,
        "size": len(content),
        "data": content,
        "created_at": datetime.now(timezone.utc),
    }
    result = await db.appointment_attachments.insert_one(document)
    return AppointmentAttachment(
        id=str(result.inserted_id),
        file_name=document["file_name"],
        content_type=document["content_type"],
        size=document["size"],
    )


@router.post("", response_model=Appointment, status_code=201)
async def create_appointment(payload: AppointmentCreate) -> Appointment:
    validate_requested_date(payload.preferred_date)
    if payload.preferred_time not in AVAILABLE_TIMES and payload.preferred_time not in LEGACY_TIME_PREFERENCES:
        raise HTTPException(status_code=422, detail="Please choose an available time between 10:00 AM and 6:00 PM.")
    if payload.attachment_ids:
        try:
            object_ids = [ObjectId(value) for value in payload.attachment_ids]
        except Exception as exc:
            raise HTTPException(status_code=422, detail="One or more attachment references are invalid.") from exc
        attachment_count = await db.appointment_attachments.count_documents({"_id": {"$in": object_ids}})
        if attachment_count != len(object_ids):
            raise HTTPException(status_code=422, detail="One or more attachments could not be found.")
    appointment = Appointment(
        **payload.model_dump(),
        reference=f"AMY-{secrets.token_hex(3).upper()}",
    )
    await db.appointments.insert_one(appointment.model_dump())
    return appointment