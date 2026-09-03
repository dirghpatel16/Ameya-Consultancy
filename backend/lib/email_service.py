import email.mime.multipart
import email.mime.text
import logging
import os
import smtplib
import urllib.parse
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

DOCTOR_TEST_EMAIL = os.environ.get("DOCTOR_EMAIL", "dirgh8011patel@gmail.com")
CLINIC_NAME = "Ameya Consultancy — Her Health Connect"
CLINIC_PHONE = "+91 63557 34167"
CLINIC_ADDRESS = "Ameya Consultancy, Gujarat, India"


def build_ics_calendar(
    appointment_id: str,
    patient_name: str,
    patient_email: str,
    consultation_type: str,
    focus_area: str,
    preferred_date: str,
    preferred_time: str,
    meeting_url: str | None,
    reference: str,
) -> str:
    """
    Build RFC 5545 compliant iCalendar (.ics) string with METHOD:REQUEST
    so Gmail/Google Calendar renders native Yes/No/Maybe RSVP buttons.
    """
    # Parse date and time into start/end datetime
    try:
        # preferred_date: 'YYYY-MM-DD', preferred_time: '11:00 AM'
        time_part = preferred_time.strip()
        dt_str = f"{preferred_date} {time_part}"
        start_dt = datetime.strptime(dt_str, "%Y-%m-%d %I:%M %p")
    except Exception:
        # Fallback to noon if parsing fails
        start_dt = datetime.strptime(f"{preferred_date} 12:00 PM", "%Y-%m-%d %I:%M %p")

    end_dt = start_dt + timedelta(minutes=45)
    now_utc = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    dt_start_str = start_dt.strftime("%Y%m%dT%H%M00")
    dt_end_str = end_dt.strftime("%Y%m%dT%H%M00")

    is_virtual = consultation_type == "video_consultation"
    type_label = "Virtual Consultation (Google Meet)" if is_virtual else "In-Person Clinic Visit"
    location = meeting_url if (is_virtual and meeting_url) else CLINIC_ADDRESS

    summary = f"Consultation: {patient_name} & Dr. Nisha Ghelani"
    description = (
        f"Ameya Consultancy — Her Health Connect\\n"
        f"Patient: {patient_name}\\n"
        f"Type: {type_label}\\n"
        f"Care Pathway: {focus_area}\\n"
        f"Reference: {reference}\\n"
        f"Video Link: {meeting_url if meeting_url else 'N/A'}\\n"
        f"Phone: {CLINIC_PHONE}\\n"
        f"Please join 5 minutes before scheduled time."
    )

    ics_content = (
        "BEGIN:VCALENDAR\r\n"
        "VERSION:2.0\r\n"
        "PRODID:-//Ameya Consultancy//Her Health Connect//EN\r\n"
        "CALSCALE:GREGORIAN\r\n"
        "METHOD:REQUEST\r\n"
        "BEGIN:VTIMEZONE\r\n"
        "TZID:Asia/Kolkata\r\n"
        "BEGIN:STANDARD\r\n"
        "DTSTART:19700101T000000\r\n"
        "TZOFFSETFROM:+0530\r\n"
        "TZOFFSETTO:+0530\r\n"
        "TZNAME:IST\r\n"
        "END:STANDARD\r\n"
        "END:VTIMEZONE\r\n"
        "BEGIN:VEVENT\r\n"
        f"UID:{reference}-{appointment_id}@ameya-consultancy.vercel.app\r\n"
        f"DTSTAMP:{now_utc}\r\n"
        f"DTSTART;TZID=Asia/Kolkata:{dt_start_str}\r\n"
        f"DTEND;TZID=Asia/Kolkata:{dt_end_str}\r\n"
        f"SUMMARY:{summary}\r\n"
        f"DESCRIPTION:{description}\r\n"
        f"LOCATION:{location}\r\n"
        f"ORGANIZER;CN=\"Dr. Nisha Ghelani (Ameya Consultancy)\":mailto:{DOCTOR_TEST_EMAIL}\r\n"
        f"ATTENDEE;CUTYPE=INDIVIDUAL;ROLE=REQ-PARTICIPANT;PARTSTAT=NEEDS-ACTION;RSVP=TRUE;CN=\"{patient_name}\":mailto:{patient_email}\r\n"
        "STATUS:CONFIRMED\r\n"
        "SEQUENCE:0\r\n"
        "END:VEVENT\r\n"
        "END:VCALENDAR\r\n"
    )
    return ics_content


def build_google_calendar_url(
    patient_name: str,
    consultation_type: str,
    focus_area: str,
    preferred_date: str,
    preferred_time: str,
    meeting_url: str | None,
    reference: str,
) -> str:
    """Generate a one-click Google Calendar web link."""
    try:
        dt_str = f"{preferred_date} {preferred_time.strip()}"
        start_dt = datetime.strptime(dt_str, "%Y-%m-%d %I:%M %p")
    except Exception:
        start_dt = datetime.strptime(f"{preferred_date} 12:00 PM", "%Y-%m-%d %I:%M %p")

    end_dt = start_dt + timedelta(minutes=45)
    # Convert IST (+05:30) to UTC for Google Calendar URL
    start_utc = start_dt - timedelta(hours=5, minutes=30)
    end_utc = end_dt - timedelta(hours=5, minutes=30)
    dates = f"{start_utc.strftime('%Y%m%dT%H%M%SZ')}/{end_utc.strftime('%Y%m%dT%H%M%SZ')}"

    is_virtual = consultation_type == "video_consultation"
    location = meeting_url if (is_virtual and meeting_url) else CLINIC_ADDRESS

    title = f"Dr. Nisha Ghelani & {patient_name} — Consultation"
    details = (
        f"Ameya Consultancy — Women's Health Consultation\n"
        f"Reference: {reference}\n"
        f"Type: {'Virtual (Google Meet)' if is_virtual else 'In-Person Clinic Visit'}\n"
        f"Care Focus: {focus_area}\n"
        f"{'Join Google Meet: ' + meeting_url if meeting_url else 'Location: ' + CLINIC_ADDRESS}\n"
        f"Contact: {CLINIC_PHONE}"
    )

    params = {
        "action": "TEMPLATE",
        "text": title,
        "dates": dates,
        "details": details,
        "location": location,
        "sprop": "website:ameya-consultancy.vercel.app",
    }
    return f"https://calendar.google.com/calendar/render?{urllib.parse.urlencode(params)}"


def build_whatsapp_message(
    patient_name: str,
    consultation_type: str,
    focus_area: str,
    preferred_date: str,
    preferred_time: str,
    meeting_url: str | None,
    reference: str,
) -> str:
    """Generate pre-filled WhatsApp message for patient confirmation."""
    is_virtual = consultation_type == "video_consultation"
    type_str = "🌐 Virtual (Google Meet)" if is_virtual else "🏥 In-Person Clinic Visit"
    msg = (
        f"Hello Dr. Nisha,\n\n"
        f"I have booked a consultation with Ameya Consultancy.\n\n"
        f"📋 *Reference:* {reference}\n"
        f"👤 *Patient Name:* {patient_name}\n"
        f"🩺 *Care Focus:* {focus_area}\n"
        f"📍 *Type:* {type_str}\n"
        f"📅 *Date:* {preferred_date}\n"
        f"⏰ *Time:* {preferred_time} (IST)\n"
    )
    if is_virtual and meeting_url:
        msg += f"🔗 *Google Meet Link:* {meeting_url}\n"
    msg += "\nLooking forward to the consultation."
    return msg


async def send_appointment_emails(
    appointment_id: str,
    patient_name: str,
    patient_email: str,
    patient_phone: str,
    consultation_type: str,
    focus_area: str,
    preferred_date: str,
    preferred_time: str,
    notes: str,
    meeting_url: str | None,
    reference: str,
) -> bool:
    """
    Send confirmation email with interactive Google Calendar invite (.ics)
    to both patient and doctor (dirgh8011patel@gmail.com).
    """
    is_virtual = consultation_type == "video_consultation"
    type_label = "Virtual Consultation (Google Meet)" if is_virtual else "In-Person Clinic Visit"

    ics_content = build_ics_calendar(
        appointment_id=appointment_id,
        patient_name=patient_name,
        patient_email=patient_email,
        consultation_type=consultation_type,
        focus_area=focus_area,
        preferred_date=preferred_date,
        preferred_time=preferred_time,
        meeting_url=meeting_url,
        reference=reference,
    )

    # 1. Render Patient HTML email (patient-focused voice)
    patient_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #FAF8F5; margin: 0; padding: 20px; color: #2B2D42; }}
        .container {{ max-width: 600px; margin: 0 auto; background: #FFFFFF; border-radius: 16px; overflow: hidden; border: 1px solid #E5DEC9; }}
        .header {{ background-color: #164D59; padding: 28px; text-align: center; color: #FFFFFF; }}
        .header h1 {{ margin: 0; font-size: 24px; font-weight: 600; letter-spacing: -0.5px; }}
        .header p {{ margin: 6px 0 0 0; font-size: 12px; text-transform: uppercase; letter-spacing: 2px; color: #8FD5E1; }}
        .content {{ padding: 32px 28px; }}
        .badge {{ display: inline-block; background-color: #EAF2F1; color: #0E776C; font-weight: bold; font-size: 12px; padding: 4px 12px; border-radius: 12px; margin-bottom: 16px; }}
        .ref-box {{ background-color: #F4F1E8; border-radius: 12px; padding: 18px; margin: 20px 0; }}
        .ref-label {{ font-size: 11px; text-transform: uppercase; letter-spacing: 1.5px; color: #839788; font-weight: bold; }}
        .ref-code {{ font-size: 22px; font-family: monospace; font-weight: bold; color: #164D59; margin: 4px 0 0 0; }}
        .detail-row {{ margin: 12px 0; font-size: 15px; }}
        .detail-label {{ font-weight: bold; color: #52706B; }}
        .btn {{ display: inline-block; background-color: #0E776C; color: #FFFFFF !important; text-decoration: none; padding: 14px 28px; border-radius: 8px; font-weight: bold; font-size: 15px; margin-top: 20px; text-align: center; }}
        .footer {{ background-color: #F4F1E8; padding: 20px 28px; text-align: center; font-size: 12px; color: #839788; border-top: 1px solid #E5DEC9; }}
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          <h1>Ameya Consultancy</h1>
          <p>Her Health Connect · Dr. Nisha Ghelani</p>
        </div>
        <div class="content">
          <span class="badge">Appointment Confirmed</span>
          <h2 style="color: #164D59; margin-top: 0;">Hello {patient_name},</h2>
          <p style="font-size: 15px; line-height: 1.6; color: #35504D;">
            Your consultation with <strong>Dr. Nisha Ghelani</strong>, MD (Ob & Gyn) has been confirmed.
            An interactive Google Calendar invite (.ics) has been attached to this email so you can RSVP and add it to your calendar with one click.
          </p>
          
          <div class="ref-box">
            <div class="ref-label">Booking Reference</div>
            <div class="ref-code">{reference}</div>
          </div>

          <div class="detail-row"><span class="detail-label">Consultation Type:</span> {type_label}</div>
          <div class="detail-row"><span class="detail-label">Care Pathway:</span> {focus_area}</div>
          <div class="detail-row"><span class="detail-label">Date:</span> {preferred_date}</div>
          <div class="detail-row"><span class="detail-label">Time:</span> {preferred_time} (India IST)</div>
          <p style="font-size: 12px; color: #839788; margin-top: 2px;">
            (The attached calendar invite automatically converts this meeting to your local timezone.)
          </p>

          {f'''
          <div style="margin-top: 24px; padding: 18px; background: #EAF2F1; border-radius: 12px; border: 1px solid #B8DAD2;">
            <p style="margin: 0 0 10px 0; font-weight: bold; color: #164D59;">Your Google Meet Video Link:</p>
            <a href="{meeting_url}" style="color: #0E776C; font-weight: bold; font-size: 15px; word-break: break-all;">{meeting_url}</a>
            <div style="text-align: center; margin-top: 16px;">
              <a href="{meeting_url}" class="btn">Join Google Meet</a>
            </div>
          </div>
          ''' if is_virtual and meeting_url else f'''
          <div style="margin-top: 24px; padding: 18px; background: #F4F1E8; border-radius: 12px; border: 1px solid #E5DEC9;">
            <p style="margin: 0; font-weight: bold; color: #164D59;">Clinic Location:</p>
            <p style="margin: 6px 0 0 0; color: #52706B; font-size: 14px;">{CLINIC_ADDRESS}</p>
          </div>
          '''}

          <p style="margin-top: 28px; font-size: 13px; color: #839788; line-height: 1.5;">
            Need to reschedule or have questions? Contact Dr. Nisha on WhatsApp or call <strong>{CLINIC_PHONE}</strong>.
          </p>
        </div>
        <div class="footer">
          Ameya Consultancy · Dr. Nisha Ghelani, MD (Ob & Gyn)<br>
          Private care for every chapter of her health.
        </div>
      </div>
    </body>
    </html>
    """

    # 2. Render Doctor HTML email (doctor-focused alert voice)
    doctor_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #FAF8F5; margin: 0; padding: 20px; color: #2B2D42; }}
        .container {{ max-width: 600px; margin: 0 auto; background: #FFFFFF; border-radius: 16px; overflow: hidden; border: 1px solid #E5DEC9; }}
        .header {{ background-color: #164D59; padding: 28px; text-align: center; color: #FFFFFF; }}
        .header h1 {{ margin: 0; font-size: 24px; font-weight: 600; letter-spacing: -0.5px; }}
        .header p {{ margin: 6px 0 0 0; font-size: 12px; text-transform: uppercase; letter-spacing: 2px; color: #8FD5E1; }}
        .content {{ padding: 32px 28px; }}
        .badge {{ display: inline-block; background-color: #EAF2F1; color: #0E776C; font-weight: bold; font-size: 12px; padding: 4px 12px; border-radius: 12px; margin-bottom: 16px; }}
        .ref-box {{ background-color: #F4F1E8; border-radius: 12px; padding: 18px; margin: 20px 0; }}
        .ref-label {{ font-size: 11px; text-transform: uppercase; letter-spacing: 1.5px; color: #839788; font-weight: bold; }}
        .ref-code {{ font-size: 22px; font-family: monospace; font-weight: bold; color: #164D59; margin: 4px 0 0 0; }}
        .detail-row {{ margin: 12px 0; font-size: 15px; }}
        .detail-label {{ font-weight: bold; color: #52706B; }}
        .btn {{ display: inline-block; background-color: #0E776C; color: #FFFFFF !important; text-decoration: none; padding: 14px 28px; border-radius: 8px; font-weight: bold; font-size: 15px; margin-top: 20px; text-align: center; }}
        .footer {{ background-color: #F4F1E8; padding: 20px 28px; text-align: center; font-size: 12px; color: #839788; border-top: 1px solid #E5DEC9; }}
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          <h1>Ameya Consultancy</h1>
          <p>New Appointment Alert · Doctor Portal</p>
        </div>
        <div class="content">
          <span class="badge">New Consultation Booked</span>
          <h2 style="color: #164D59; margin-top: 0;">Hello Dr. Nisha,</h2>
          <p style="font-size: 15px; line-height: 1.6; color: #35504D;">
            A new patient has booked a consultation through the Ameya Consultancy website.
          </p>
          
          <div class="ref-box">
            <div class="ref-label">Booking Reference</div>
            <div class="ref-code">{reference}</div>
          </div>

          <div class="detail-row"><span class="detail-label">Patient Name:</span> {patient_name}</div>
          <div class="detail-row"><span class="detail-label">Patient Phone:</span> {patient_phone}</div>
          <div class="detail-row"><span class="detail-label">Patient Email:</span> {patient_email}</div>
          <div class="detail-row"><span class="detail-label">Care Pathway:</span> {focus_area}</div>
          <div class="detail-row"><span class="detail-label">Consultation Date:</span> {preferred_date}</div>
          <div class="detail-row"><span class="detail-label">Consultation Time:</span> {preferred_time} (IST)</div>
          {f'<div class="detail-row"><span class="detail-label">Patient Notes / Concern:</span> {notes}</div>' if notes else '<div class="detail-row"><span class="detail-label">Patient Notes:</span> None provided</div>'}

          {f'''
          <div style="margin-top: 24px; padding: 18px; background: #EAF2F1; border-radius: 12px; border: 1px solid #B8DAD2;">
            <p style="margin: 0 0 10px 0; font-weight: bold; color: #164D59;">Google Meet Video Room:</p>
            <a href="{meeting_url}" style="color: #0E776C; font-weight: bold; font-size: 15px; word-break: break-all;">{meeting_url}</a>
            <div style="text-align: center; margin-top: 16px;">
              <a href="{meeting_url}" class="btn">Join Google Meet</a>
            </div>
            <p style="margin: 12px 0 0 0; font-size: 12px; color: #52706B;">
              ✅ This consultation has been automatically scheduled in your Google Calendar.
            </p>
          </div>
          ''' if is_virtual and meeting_url else ''}
        </div>
        <div class="footer">
          Ameya Consultancy Notification Engine<br>
          Automated alert for Dr. Nisha Ghelani
        </div>
      </div>
    </body>
    </html>
    """

    patient_subject = f"Confirmed: Your Consultation with Dr. Nisha Ghelani ({reference})"
    doctor_subject = f"📅 New Booking: {patient_name} — {preferred_date} at {preferred_time} ({reference})"
    from_email = os.environ.get("RESEND_FROM_EMAIL", "Ameya Consultancy <onboarding@resend.dev>")

    import base64
    import json
    import urllib.request
    import urllib.error
    import ssl

    b64_ics = base64.b64encode(ics_content.encode("utf-8")).decode("utf-8")
    resend_key = os.environ.get("RESEND_API_KEY")

    def _send_resend(recipient: str, subject: str, html_body: str) -> bool:
        if not resend_key:
            return False
        payload = {
            "from": from_email,
            "to": [recipient],
            "subject": subject,
            "html": html_body,
            "attachments": [
                {
                    "filename": "consultation.ics",
                    "content": b64_ics,
                }
            ],
        }
        req = urllib.request.Request(
            "https://api.resend.com/emails",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {resend_key}",
                "Content-Type": "application/json",
                "User-Agent": "AmeyaConsultancy/1.0",
            },
            method="POST",
        )
        try:
            ssl_ctx = ssl.create_default_context()
        except Exception:
            ssl_ctx = ssl._create_unverified_context()

        try:
            with urllib.request.urlopen(req, timeout=10, context=ssl_ctx) as resp:
                logger.info("Resend successfully sent to %s (status: %s)", recipient, resp.status)
                return True
        except urllib.error.URLError:
            with urllib.request.urlopen(req, timeout=10, context=ssl._create_unverified_context()) as resp:
                logger.info("Resend sent to %s (unverified SSL, status: %s)", recipient, resp.status)
                return True

    # 1. Send Doctor Email (Doctor Voice) -> to DOCTOR_TEST_EMAIL
    doctor_sent = False
    try:
        doctor_sent = _send_resend(DOCTOR_TEST_EMAIL, doctor_subject, doctor_html)
    except Exception as exc:
        logger.warning("Failed to send doctor email to %s: %s", DOCTOR_TEST_EMAIL, exc)

    # 2. Send Patient Email (Patient Voice) -> to patient_email
    patient_sent = False
    try:
        patient_sent = _send_resend(patient_email, patient_subject, patient_html)
    except urllib.error.HTTPError as http_err:
        logger.warning("Resend rejected patient email %s (domain unverified sandbox limitation): %s", patient_email, http_err)
    except Exception as exc:
        logger.warning("Failed to send patient email to %s: %s", patient_email, exc)

    return doctor_sent or patient_sent

    logger.info(
        "Email notification generated for %s and %s (SMTP not configured, falling back to calendar and WhatsApp URLs).",
        patient_email,
        DOCTOR_TEST_EMAIL,
    )
    return False
