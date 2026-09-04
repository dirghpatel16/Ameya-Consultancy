from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
import uuid

from pydantic import BaseModel, EmailStr, Field


ConsultationType = Literal["clinic_visit", "video_consultation", "second_opinion"]


class AppointmentCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    phone: str = Field(min_length=7, max_length=30)
    consultation_type: ConsultationType
    focus_area: str = Field(min_length=2, max_length=120)
    preferred_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    preferred_time: str = Field(min_length=2, max_length=40)
    notes: str = Field(default="", max_length=1000)
    attachment_ids: list[str] = Field(default_factory=list, max_length=3)
    razorpay_order_id: str | None = None
    razorpay_payment_id: str | None = None
    razorpay_signature: str | None = None


class Appointment(AppointmentCreate):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    reference: str
    status: Literal["requested"] = "requested"
    meeting_status: Literal["pending_connection", "scheduled"] = "scheduled"
    meeting_url: str | None = None
    calendar_url: str | None = None
    whatsapp_url: str | None = None
    payment_status: Literal["paid", "pending", "exempt"] = "paid"
    payment_id: str | None = None
    amount_paid: int = 1000
    currency: str = "INR"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AvailableDate(BaseModel):
    date: str
    day_label: str
    display_label: str


class BookingOptions(BaseModel):
    timezone: str
    available_days: list[str]
    available_dates: list[AvailableDate]
    available_times: list[str]
    google_meet_enabled: bool
    consultation_fee_inr: int = 1000
    booked_slots: dict[str, list[str]] = Field(default_factory=dict)


class CreateOrderRequest(BaseModel):
    consultation_type: ConsultationType
    focus_area: str
    preferred_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    preferred_time: str = Field(min_length=2, max_length=40)
    full_name: str
    email: EmailStr
    phone: str


class CreateOrderResponse(BaseModel):
    order_id: str
    amount: int
    amount_inr: int
    currency: str
    key_id: str


class AppointmentAttachment(BaseModel):
    id: str
    file_name: str
    content_type: str
    size: int