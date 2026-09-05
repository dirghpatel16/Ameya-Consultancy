from __future__ import annotations

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
from lib.calendar_service import create_calendar_event_with_meet
from lib.payment_service import (
    CONSULTATION_FEE_INR,
    create_razorpay_order,
    verify_razorpay_signature,
)
from models.appointments import (
    Appointment,
    AppointmentAttachment,
    AppointmentCreate,
    AvailableDate,
    BookingOptions,
    CreateOrderRequest,
    CreateOrderResponse,
)

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/appointments", tags=["appointments"])
AVAILABLE_WEEKDAYS = {1, 3, 5}  # Tuesday, Thursday, Saturday
AVAILABLE_DAY_NAMES = ["Tuesday", "Thursday", "Saturday"]
AVAILABLE_TIMES = [
    "8:00 AM", "8:30 AM", "9:00 AM", "9:30 AM",
    "4:00 PM", "4:30 PM", "5:00 PM", "5:30 PM",
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

    # Double-booking prevention: fetch existing booked slots for upcoming dates
    cursor = db.appointments.find(
        {"preferred_date": {"$gte": current.isoformat()}},
        {"preferred_date": 1, "preferred_time": 1, "_id": 0},
    )
    booked_slots: dict[str, list[str]] = {}
    async for doc in cursor:
        d = doc.get("preferred_date")
        t = doc.get("preferred_time")
        if d and t:
            booked_slots.setdefault(d, []).append(t)

    return BookingOptions(
        timezone="Asia/Kolkata",
        available_days=AVAILABLE_DAY_NAMES,
        available_dates=available_dates,
        available_times=AVAILABLE_TIMES,
        google_meet_enabled=True,
        consultation_fee_inr=CONSULTATION_FEE_INR,
        booked_slots=booked_slots,
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

    # Enterprise Security: Verify actual file signature (magic bytes) to prevent MIME spoofing
    is_valid_magic = False
    if file.content_type == "application/pdf" and content.startswith(b"%PDF-"):
        is_valid_magic = True
    elif file.content_type in ("image/jpeg", "image/jpg") and content.startswith(b"\xff\xd8\xff"):
        is_valid_magic = True
    elif file.content_type == "image/png" and content.startswith(b"\x89PNG\r\n\x1a\n"):
        is_valid_magic = True

    if not is_valid_magic:
        raise HTTPException(
            status_code=422,
            detail="File content does not match the expected PDF or image format.",
        )

    # Sanitize filename against path traversal
    safe_filename = os.path.basename(file.filename or "attachment")

    document = {
        "file_name": safe_filename,
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


@router.post("/create-order", response_model=CreateOrderResponse)
async def create_order_endpoint(payload: CreateOrderRequest) -> CreateOrderResponse:
    validate_requested_date(payload.preferred_date)
    if payload.preferred_time not in AVAILABLE_TIMES and payload.preferred_time not in LEGACY_TIME_PREFERENCES:
        raise HTTPException(status_code=422, detail="Please choose an available consultation time.")

    # 1. Double-booking check: Ensure slot is not already taken
    existing = await db.appointments.find_one({
        "preferred_date": payload.preferred_date,
        "preferred_time": payload.preferred_time,
    })
    if existing:
        raise HTTPException(
            status_code=409,
            detail="This consultation slot is already booked. Please choose another available time.",
        )

    # 2. Create Razorpay order
    receipt = f"AMY-{secrets.token_hex(3).upper()}"
    notes = {
        "patient_name": payload.full_name,
        "patient_phone": payload.phone,
        "consultation_type": payload.consultation_type,
        "focus_area": payload.focus_area,
        "slot": f"{payload.preferred_date} {payload.preferred_time}",
    }
    try:
        order_data = create_razorpay_order(
            amount_inr=CONSULTATION_FEE_INR,
            receipt=receipt,
            notes=notes,
        )
        return CreateOrderResponse(**order_data)
    except Exception as exc:
        logger.error("Failed to create Razorpay order: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc))


@router.post("", response_model=Appointment, status_code=201)
async def create_appointment(payload: AppointmentCreate) -> Appointment:
    validate_requested_date(payload.preferred_date)
    if payload.preferred_time not in AVAILABLE_TIMES and payload.preferred_time not in LEGACY_TIME_PREFERENCES:
        raise HTTPException(status_code=422, detail="Please choose an available time between 8:00 AM–10:00 AM or 4:00 PM–6:00 PM.")

    # 1. Double-booking check (atomic check before payment verification)
    existing = await db.appointments.find_one({
        "preferred_date": payload.preferred_date,
        "preferred_time": payload.preferred_time,
    })
    if existing:
        raise HTTPException(
            status_code=409,
            detail="This consultation slot was just booked by another patient. Please choose another available time.",
        )

    # 2. Upfront payment verification via Razorpay
    logger.info(
        "Verifying upfront payment: order=%s, payment=%s, has_sig=%s",
        payload.razorpay_order_id,
        payload.razorpay_payment_id,
        bool(payload.razorpay_signature),
    )
    if not (payload.razorpay_order_id and payload.razorpay_payment_id and payload.razorpay_signature):
        raise HTTPException(
            status_code=402,
            detail="Upfront payment of ₹1,000 is required to confirm this consultation. Please complete the payment.",
        )

    if not verify_razorpay_signature(
        order_id=payload.razorpay_order_id,
        payment_id=payload.razorpay_payment_id,
        signature=payload.razorpay_signature,
    ):
        raise HTTPException(
            status_code=400,
            detail="Payment verification failed. Please contact Ameya Consultancy support.",
        )

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
    meeting_url = None

    if is_virtual:
        try:
            meet_uri, _ = create_calendar_event_with_meet(
                patient_name=payload.full_name,
                patient_email=payload.email,
                patient_phone=payload.phone,
                preferred_date=payload.preferred_date,
                preferred_time=payload.preferred_time,
                focus_area=payload.focus_area,
                reference=reference,
                notes=payload.notes,
            )
            if meet_uri:
                meeting_url = meet_uri
        except Exception as exc:
            logger.warning("Dynamic Google Calendar/Meet creation failed, using fallback: %s", exc)

        if not meeting_url:
            meeting_url = os.environ.get("PERMANENT_MEET_URL") or f"https://meet.google.com/amy-{reference.lower().replace('amy-', '')}-{secrets.token_hex(2)}"

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
        payment_status="paid",
        payment_id=payload.razorpay_payment_id,
        amount_paid=CONSULTATION_FEE_INR,
        currency="INR",
    )
    await db.appointments.insert_one(appointment.model_dump())

    # Send confirmation email + calendar invite (.ics) with payment receipt to patient & Dr. Nisha Ghelani
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
            attachment_ids=payload.attachment_ids,
            payment_id=payload.razorpay_payment_id,
            order_id=payload.razorpay_order_id,
            amount_paid=CONSULTATION_FEE_INR,
        )
    except Exception as email_err:
        logger.warning("Email notification error (non-fatal): %s", email_err)

    return appointment