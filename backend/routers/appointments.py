from datetime import date, datetime, timedelta, timezone
import os
import secrets

import logging
import urllib.parse

from bson import ObjectId
from fastapi import APIRouter, File, HTTPException, UploadFile

from lib.dates import today_iso
from lib.db import db
from lib.email_service import build_google_calendar_url, build_whatsapp_message, send_appointment_emails
from models.appointments import Appointment, AppointmentAttachment, AppointmentCreate, AvailableDate, BookingOptions

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/appointments", tags=["appointments"])
AVAILABLE_WEEKDAYS = {1, 3, 5}  # Tuesday, Thursday, Saturday
AVAILABLE_DAY_NAMES = ["Tuesday", "Thursday", "Saturday"]
AVAILABLE_TIMES = [
    "10:00 AM", "11:00 AM", "12:00 PM", "1:00 PM", "2:00 PM",
    "3:00 PM", "4:00 PM", "5:00 PM", "6:00 PM",
]
LEGACY_TIME_PREFERENCES = {"Morning preference", "Afternoon preference", "Evening preference"}
ALLOWED_ATTACHMENT_TYPES = {"application/pdf", "image/jpeg", "image/png"}
MAX_ATTACHMENT_BYTES = 4 * 1024 * 1024


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
        google_meet_enabled=True,
    )


@router.post("/attachments", response_model=AppointmentAttachment, status_code=201)
async def upload_appointment_attachment(file: UploadFile = File(...)) -> AppointmentAttachment:
    if file.content_type not in ALLOWED_ATTACHMENT_TYPES:
        raise HTTPException(status_code=422, detail="Only PDF, JPG, and PNG files are supported.")
    content = await file.read(MAX_ATTACHMENT_BYTES + 1)
    await file.close()
    if len(content) > MAX_ATTACHMENT_BYTES:
        raise HTTPException(status_code=413, detail="Each attachment must be 4 MB or smaller.")
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
    reference = f"AMY-{secrets.token_hex(3).upper()}"
    is_virtual = payload.consultation_type == "video_consultation"
    meeting_url = f"https://meet.google.com/amy-{reference.lower().replace('amy-', '')}-{secrets.token_hex(2)}" if is_virtual else None

    calendar_url = build_google_calendar_url(
        patient_name=payload.full_name,
        consultation_type=payload.consultation_type,
        focus_area=payload.focus_area,
        preferred_date=payload.preferred_date,
        preferred_time=payload.preferred_time,
        meeting_url=meeting_url,
        reference=reference,
    )

    wa_text = build_whatsapp_message(
        patient_name=payload.full_name,
        consultation_type=payload.consultation_type,
        focus_area=payload.focus_area,
        preferred_date=payload.preferred_date,
        preferred_time=payload.preferred_time,
        meeting_url=meeting_url,
        reference=reference,
    )
    whatsapp_url = f"https://wa.me/916355734167?text={urllib.parse.quote(wa_text)}"

    appointment = Appointment(
        **payload.model_dump(),
        reference=reference,
        meeting_status="scheduled",
        meeting_url=meeting_url,
        calendar_url=calendar_url,
        whatsapp_url=whatsapp_url,
    )
    await db.appointments.insert_one(appointment.model_dump())

    # Send confirmation email + calendar invite (.ics) to patient & dirgh8011patel@gmail.com
    try:
        await send_appointment_emails(
            appointment_id=appointment.id,
            patient_name=payload.full_name,
            patient_email=payload.email,
            patient_phone=payload.phone,
            consultation_type=payload.consultation_type,
            focus_area=payload.focus_area,
            preferred_date=payload.preferred_date,
            preferred_time=payload.preferred_time,
            notes=payload.notes,
            meeting_url=meeting_url,
            reference=reference,
        )
    except Exception as email_err:
        logger.warning("Email notification error (non-fatal): %s", email_err)

    return appointment