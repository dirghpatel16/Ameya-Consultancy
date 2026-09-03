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


class Appointment(AppointmentCreate):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    reference: str
    status: Literal["requested"] = "requested"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))