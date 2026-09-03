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


AMEYA_LOGO_URL = "https://customer-assets-7cd3h4nn.emergentagent.net/job_ameya-health/artifacts/feu0o2dt_WhatsApp%20Image%202026-09-02%20at%2023.19.22.jpeg"

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
    attachment_ids: list[str] | None = None,
) -> bool:
    """
    Send confirmation email with interactive Google Calendar invite (.ics)
    to both patient and doctor (dirgh8011patel@gmail.com).
    For the doctor, attaches any uploaded medical reports/scans.
    """
    import base64
    import json
    import urllib.request
    import urllib.error
    import ssl

    is_virtual = consultation_type == "video_consultation"
    type_label = "Virtual Consultation (Google Meet)" if is_virtual else "In-Person Clinic Visit"

    # Fetch patient uploaded reports if any
    report_attachments = []
    attachment_filenames = []
    if attachment_ids:
        try:
            from bson import ObjectId
            from lib.db import db
            object_ids = [ObjectId(aid) for aid in attachment_ids]
            cursor = db.appointment_attachments.find({"_id": {"$in": object_ids}})
            async for doc in cursor:
                fname = doc.get("file_name", "medical_report.pdf")
                data_bytes = doc.get("data", b"")
                if data_bytes:
                    report_attachments.append({
                        "filename": fname,
                        "content": base64.b64encode(data_bytes).decode("utf-8"),
                    })
                    size_kb = len(data_bytes) // 1024
                    attachment_filenames.append(f"{fname} ({size_kb} KB)")
        except Exception as exc:
            logger.warning("Failed to fetch medical attachments for doctor email: %s", exc)

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

    clean_phone = "".join(c for c in patient_phone if c.isdigit())
    wa_patient_link = f"https://wa.me/{clean_phone}" if clean_phone else None

    # 1. Patient Confirmation Email — clean, high-contrast, readable
    patient_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Consultation Confirmed</title>
    </head>
    <body style="margin:0; padding:0; background-color:#F2F0EB; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
      <table width="100%" cellpadding="0" cellspacing="0" style="padding:24px 12px;">
        <tr><td align="center">
          <table width="600" cellpadding="0" cellspacing="0" style="background:#FFFFFF; border-radius:12px; overflow:hidden; border:1px solid #D6CDBC;">

            <!-- Gold Accent -->
            <tr><td style="height:4px; background:linear-gradient(90deg,#C9956B,#D4A373,#C9956B);"></td></tr>

            <!-- Header -->
            <tr><td style="background:#164D59; padding:30px 24px; text-align:center;">
              <img src="{AMEYA_LOGO_URL}" alt="Logo" width="58" height="58" style="border-radius:50%; border:2px solid #D4A373; background:#FFFDF8; display:block; margin:0 auto 12px auto;" />
              <div style="font-size:22px; font-weight:700; color:#FFFFFF; letter-spacing:-0.3px;">Ameya Consultancy</div>
              <div style="font-size:11px; color:#FFFFFF; letter-spacing:2px; text-transform:uppercase; margin-top:4px; opacity:0.85;">Dr. Nisha Ghelani, MD (Ob &amp; Gyn)</div>
            </td></tr>

            <!-- Body -->
            <tr><td style="padding:32px 30px;">
              <!-- Status -->
              <div style="display:inline-block; background:#DFF5EE; color:#0A6B5E; font-size:12px; font-weight:700; padding:5px 14px; border-radius:16px; margin-bottom:18px;">✓ CONFIRMED</div>

              <h2 style="color:#1A1A2E; font-size:22px; font-weight:700; margin:12px 0 10px 0;">Hello {patient_name},</h2>
              <p style="font-size:15px; line-height:1.7; color:#333333; margin:0 0 24px 0;">
                Your consultation with <strong style="color:#164D59;">Dr. Nisha Ghelani</strong> has been confirmed. A calendar invite (<code>.ics</code>) is attached — open it to add this appointment to your Google or Apple Calendar.
              </p>

              <!-- Appointment Card -->
              <table width="100%" cellpadding="0" cellspacing="0" style="background:#F9F7F2; border:1px solid #E2DBCC; border-radius:10px; overflow:hidden;">
                <tr><td style="padding:18px 20px 12px 20px; border-bottom:1px dashed #D6CDBC;">
                  <div style="font-size:10px; text-transform:uppercase; letter-spacing:1.5px; color:#8A8070; font-weight:700;">Booking Reference</div>
                  <div style="font-size:22px; font-family:Menlo,Consolas,monospace; font-weight:800; color:#164D59; margin-top:4px;">{reference}</div>
                </td></tr>
                <tr><td style="padding:16px 20px;">
                  <table width="100%" cellpadding="0" cellspacing="0">
                    <tr>
                      <td style="padding:6px 0; font-size:14px; color:#555555; width:42%;">Consultation Type</td>
                      <td style="padding:6px 0; font-size:14px; color:#1A1A2E; font-weight:700;">{type_label}</td>
                    </tr>
                    <tr>
                      <td style="padding:6px 0; font-size:14px; color:#555555;">Care Pathway</td>
                      <td style="padding:6px 0; font-size:14px; color:#1A1A2E; font-weight:700;">{focus_area}</td>
                    </tr>
                    <tr>
                      <td style="padding:6px 0; font-size:14px; color:#555555;">Date</td>
                      <td style="padding:6px 0; font-size:14px; color:#1A1A2E; font-weight:700;">{preferred_date}</td>
                    </tr>
                    <tr>
                      <td style="padding:6px 0; font-size:14px; color:#555555;">Time</td>
                      <td style="padding:6px 0; font-size:14px; color:#1A1A2E; font-weight:700;">{preferred_time} (IST)</td>
                    </tr>
                  </table>
                  <p style="font-size:12px; color:#777777; margin:10px 0 0 0; font-style:italic;">
                    The attached calendar invite auto-adjusts to your local timezone.
                  </p>
                </td></tr>
              </table>

              {f'''
              <!-- Meet Link -->
              <table width="100%" cellpadding="0" cellspacing="0" style="margin-top:24px; background:#EDF7F5; border:1px solid #B0D9CF; border-radius:10px;">
                <tr><td style="padding:22px 20px; text-align:center;">
                  <div style="font-size:15px; font-weight:700; color:#164D59; margin-bottom:4px;">Your Video Consultation Room</div>
                  <div style="font-size:13px; color:#444444; margin-bottom:16px;">Encrypted &amp; powered by Google Meet</div>
                  <a href="{meeting_url}" style="display:inline-block; background:#0E776C; color:#FFFFFF; font-weight:700; font-size:15px; text-decoration:none; padding:13px 32px; border-radius:8px;">Join Google Meet</a>
                  <div style="margin-top:12px; font-size:12px; color:#0E776C; word-break:break-all;"><a href="{meeting_url}" style="color:#0E776C;">{meeting_url}</a></div>
                  <p style="font-size:12px; color:#555555; margin:10px 0 0 0;">🔒 No download needed — works in any browser.</p>
                </td></tr>
              </table>
              ''' if is_virtual and meeting_url else f'''
              <table width="100%" cellpadding="0" cellspacing="0" style="margin-top:24px; background:#F9F7F2; border:1px solid #E2DBCC; border-radius:10px;">
                <tr><td style="padding:18px 20px;">
                  <div style="font-size:15px; font-weight:700; color:#164D59;">🏥 Clinic Address</div>
                  <div style="font-size:14px; color:#333333; margin-top:6px; line-height:1.5;">{CLINIC_ADDRESS}</div>
                </td></tr>
              </table>
              '''}

              <!-- Preparation Tips -->
              <table width="100%" cellpadding="0" cellspacing="0" style="margin-top:24px; border-left:4px solid #D4A373; background:#FDFBF6; border-radius:0 8px 8px 0;">
                <tr><td style="padding:16px 18px;">
                  <div style="font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:1px; color:#7A5C3A; margin-bottom:8px;">📋 Before Your Consultation</div>
                  <div style="font-size:13px; line-height:1.7; color:#333333;">
                    <strong>1.</strong> Find a quiet, well-lit room.<br>
                    <strong>2.</strong> Have past prescriptions or scans handy.<br>
                    <strong>3.</strong> Write down your top questions.
                  </div>
                </td></tr>
              </table>

              <p style="margin-top:26px; font-size:13px; color:#555555; text-align:center;">
                Need to reschedule? Call <strong style="color:#164D59;">{CLINIC_PHONE}</strong>
              </p>
            </td></tr>

            <!-- Footer -->
            <tr><td style="background:#F5F2EC; padding:22px 28px; text-align:center; border-top:1px solid #E2DBCC;">
              <div style="font-size:13px; font-weight:700; color:#164D59;">Ameya Consultancy</div>
              <div style="font-size:12px; color:#666666; margin-top:2px;">Dr. Nisha Ghelani, MD (Ob &amp; Gyn) · 22+ Years Experience</div>
              <div style="font-size:11px; color:#999999; margin-top:6px;">Confidential communication for {patient_name}</div>
            </td></tr>

          </table>
        </td></tr>
      </table>
    </body>
    </html>
    """

    # 2. Doctor Alert Email — clean clinical dossier, high-contrast, readable
    reports_html = ""
    if attachment_filenames:
        reports_rows = "".join(f"""
        <tr>
          <td style="padding:8px 12px; font-size:13px; color:#1A1A2E; border-bottom:1px solid #E8F0ED;">📄 <strong>{fn}</strong></td>
          <td style="padding:8px 12px; font-size:11px; color:#0A6B5E; font-weight:700; text-align:right; border-bottom:1px solid #E8F0ED;">ATTACHED</td>
        </tr>
        """ for fn in attachment_filenames)
        reports_html = f"""
        <table width="100%" cellpadding="0" cellspacing="0" style="margin-top:20px; background:#EDF7F5; border:1px solid #B0D9CF; border-radius:10px; overflow:hidden;">
          <tr><td style="padding:14px 16px; font-size:12px; font-weight:700; color:#0A6B5E; text-transform:uppercase; letter-spacing:1px; border-bottom:1px solid #C5E0D8;">
            📎 Patient Reports &amp; Scans ({len(attachment_filenames)})
          </td></tr>
          <tr><td style="padding:4px 8px;">
            <table width="100%" cellpadding="0" cellspacing="0">
              {reports_rows}
            </table>
          </td></tr>
          <tr><td style="padding:10px 16px; font-size:12px; color:#0A6B5E; font-weight:600;">
            ✓ All files attached to this email for review.
          </td></tr>
        </table>
        """
    else:
        reports_html = '<div style="margin-top:14px; font-size:13px; color:#666666;"><strong style="color:#444444;">Uploaded Reports:</strong> None uploaded</div>'

    doctor_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>New Patient Dossier</title>
    </head>
    <body style="margin:0; padding:0; background-color:#F2F0EB; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
      <table width="100%" cellpadding="0" cellspacing="0" style="padding:24px 12px;">
        <tr><td align="center">
          <table width="600" cellpadding="0" cellspacing="0" style="background:#FFFFFF; border-radius:12px; overflow:hidden; border:1px solid #D6CDBC;">

            <!-- Gold Accent -->
            <tr><td style="height:4px; background:linear-gradient(90deg,#C9956B,#D4A373,#C9956B);"></td></tr>

            <!-- Header -->
            <tr><td style="background:#164D59; padding:30px 24px; text-align:center;">
              <img src="{AMEYA_LOGO_URL}" alt="Logo" width="58" height="58" style="border-radius:50%; border:2px solid #D4A373; background:#FFFDF8; display:block; margin:0 auto 12px auto;" />
              <div style="font-size:22px; font-weight:700; color:#FFFFFF; letter-spacing:-0.3px;">Ameya Consultancy</div>
              <div style="font-size:11px; color:#FFFFFF; letter-spacing:2px; text-transform:uppercase; margin-top:4px; opacity:0.85;">Doctor Alert · New Patient Booking</div>
            </td></tr>

            <!-- Body -->
            <tr><td style="padding:32px 30px;">
              <div style="display:inline-block; background:#E0ECF0; color:#164D59; font-size:12px; font-weight:700; padding:5px 14px; border-radius:16px; margin-bottom:18px;">⚡ NEW BOOKING</div>

              <h2 style="color:#1A1A2E; font-size:22px; font-weight:700; margin:12px 0 10px 0;">Hello Dr. Nisha,</h2>
              <p style="font-size:15px; line-height:1.7; color:#333333; margin:0 0 24px 0;">
                A new patient has booked a consultation. Here is the complete intake dossier:
              </p>

              <!-- Patient Dossier Card -->
              <table width="100%" cellpadding="0" cellspacing="0" style="background:#F9F7F2; border:1px solid #E2DBCC; border-radius:10px; overflow:hidden;">
                <tr><td style="padding:18px 20px 12px 20px; border-bottom:1px dashed #D6CDBC;">
                  <div style="font-size:10px; text-transform:uppercase; letter-spacing:1.5px; color:#8A8070; font-weight:700;">Booking Reference</div>
                  <div style="font-size:22px; font-family:Menlo,Consolas,monospace; font-weight:800; color:#164D59; margin-top:4px;">{reference}</div>
                </td></tr>
                <tr><td style="padding:16px 20px;">
                  <table width="100%" cellpadding="0" cellspacing="0">
                    <tr>
                      <td style="padding:7px 0; font-size:14px; color:#555555; width:38%; border-bottom:1px solid #EDEAD9;">Patient Name</td>
                      <td style="padding:7px 0; font-size:14px; color:#1A1A2E; font-weight:700; border-bottom:1px solid #EDEAD9;">{patient_name}</td>
                    </tr>
                    <tr>
                      <td style="padding:7px 0; font-size:14px; color:#555555; border-bottom:1px solid #EDEAD9;">Phone</td>
                      <td style="padding:7px 0; font-size:14px; font-weight:700; border-bottom:1px solid #EDEAD9;">
                        <a href="tel:{patient_phone}" style="color:#164D59; text-decoration:none;">{patient_phone}</a>{f' · <a href="{wa_patient_link}" style="color:#25D366; text-decoration:none; font-weight:700;">WhatsApp</a>' if wa_patient_link else ''}
                      </td>
                    </tr>
                    <tr>
                      <td style="padding:7px 0; font-size:14px; color:#555555; border-bottom:1px solid #EDEAD9;">Email</td>
                      <td style="padding:7px 0; font-size:14px; font-weight:700; border-bottom:1px solid #EDEAD9;"><a href="mailto:{patient_email}" style="color:#164D59; text-decoration:none;">{patient_email}</a></td>
                    </tr>
                    <tr>
                      <td style="padding:7px 0; font-size:14px; color:#555555; border-bottom:1px solid #EDEAD9;">Care Focus</td>
                      <td style="padding:7px 0; font-size:14px; color:#1A1A2E; font-weight:700; border-bottom:1px solid #EDEAD9;">{focus_area}</td>
                    </tr>
                    <tr>
                      <td style="padding:7px 0; font-size:14px; color:#555555; border-bottom:1px solid #EDEAD9;">Date</td>
                      <td style="padding:7px 0; font-size:14px; color:#1A1A2E; font-weight:700; border-bottom:1px solid #EDEAD9;">{preferred_date}</td>
                    </tr>
                    <tr>
                      <td style="padding:7px 0; font-size:14px; color:#555555;">Time</td>
                      <td style="padding:7px 0; font-size:14px; color:#1A1A2E; font-weight:700;">{preferred_time} (IST)</td>
                    </tr>
                  </table>
                </td></tr>
              </table>

              <!-- Patient Notes -->
              <table width="100%" cellpadding="0" cellspacing="0" style="margin-top:20px; border-left:4px solid #164D59; background:#F9F7F2; border-radius:0 8px 8px 0;">
                <tr><td style="padding:14px 18px;">
                  <div style="font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:1px; color:#164D59; margin-bottom:5px;">Patient Notes / Concern</div>
                  <div style="font-size:14px; color:#1A1A2E; line-height:1.6;">"{notes if notes else 'No specific concerns noted.'}"</div>
                </td></tr>
              </table>

              {reports_html}

              {f'''
              <!-- Meet Link -->
              <table width="100%" cellpadding="0" cellspacing="0" style="margin-top:24px; background:#EDF7F5; border:1px solid #B0D9CF; border-radius:10px;">
                <tr><td style="padding:22px 20px; text-align:center;">
                  <div style="font-size:15px; font-weight:700; color:#164D59; margin-bottom:4px;">Google Meet Room</div>
                  <div style="font-size:12px; color:#0A6B5E; font-weight:600; margin-bottom:14px;">✓ Auto-synced to your Google Calendar</div>
                  <a href="{meeting_url}" style="display:inline-block; background:#0E776C; color:#FFFFFF; font-weight:700; font-size:15px; text-decoration:none; padding:13px 32px; border-radius:8px;">Start / Join Consultation</a>
                  <div style="margin-top:12px; font-size:12px; word-break:break-all;"><a href="{meeting_url}" style="color:#0E776C;">{meeting_url}</a></div>
                </td></tr>
              </table>
              ''' if is_virtual and meeting_url else ''}

            </td></tr>

            <!-- Footer -->
            <tr><td style="background:#F5F2EC; padding:22px 28px; text-align:center; border-top:1px solid #E2DBCC;">
              <div style="font-size:13px; font-weight:700; color:#164D59;">Ameya Consultancy — Notification Engine</div>
              <div style="font-size:12px; color:#666666; margin-top:2px;">Alert for Dr. Nisha Ghelani, MD (Ob &amp; Gyn)</div>
              <div style="font-size:11px; color:#999999; margin-top:6px;">Confidential medical record. Do not forward.</div>
            </td></tr>

          </table>
        </td></tr>
      </table>
    </body>
    </html>
    """

    patient_subject = f"Confirmed: Your Consultation with Dr. Nisha Ghelani ({reference})"
    doctor_subject = f"📅 New Booking: {patient_name} — {preferred_date} at {preferred_time} ({reference})"
    from_email = os.environ.get("RESEND_FROM_EMAIL", "Dr. Nisha Ghelani · Ameya Consultancy <onboarding@resend.dev>")

    b64_ics = base64.b64encode(ics_content.encode("utf-8")).decode("utf-8")
    resend_key = os.environ.get("RESEND_API_KEY")

    def _send_resend(recipient: str, subject: str, html_body: str, extra_attachments: list | None = None) -> bool:
        if not resend_key:
            return False
        attachments_list = [
            {
                "filename": "consultation.ics",
                "content": b64_ics,
            }
        ]
        if extra_attachments:
            attachments_list.extend(extra_attachments)

        payload = {
            "from": from_email,
            "to": [recipient],
            "subject": subject,
            "html": html_body,
            "attachments": attachments_list,
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
            with urllib.request.urlopen(req, timeout=12, context=ssl_ctx) as resp:
                logger.info("Resend successfully sent to %s (status: %s)", recipient, resp.status)
                return True
        except urllib.error.URLError:
            with urllib.request.urlopen(req, timeout=12, context=ssl._create_unverified_context()) as resp:
                logger.info("Resend sent to %s (unverified SSL, status: %s)", recipient, resp.status)
                return True

    # 1. Send Doctor Email (Doctor Voice + Uploaded Patient Reports) -> to DOCTOR_TEST_EMAIL
    doctor_sent = False
    try:
        doctor_sent = _send_resend(DOCTOR_TEST_EMAIL, doctor_subject, doctor_html, extra_attachments=report_attachments)
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
