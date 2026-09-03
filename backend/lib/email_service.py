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

    # 1. Render Patient HTML email (concierge patient voice)
    patient_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Consultation Confirmed - Ameya Consultancy</title>
      <style>
        body {{
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
          background-color: #F6F4EF;
          margin: 0;
          padding: 24px 12px;
          color: #2B2D42;
          -webkit-font-smoothing: antialiased;
        }}
        .wrapper {{
          max-width: 600px;
          margin: 0 auto;
          background: #FFFFFF;
          border-radius: 18px;
          overflow: hidden;
          border: 1px solid #E5DEC9;
          box-shadow: 0 10px 35px rgba(22, 77, 89, 0.08);
        }}
        .top-gold-bar {{
          height: 5px;
          background: linear-gradient(90deg, #D4A373 0%, #E8C39E 50%, #D4A373 100%);
        }}
        .header {{
          background: linear-gradient(135deg, #0F3E4D 0%, #164D59 55%, #114B5F 100%);
          padding: 34px 24px 30px;
          text-align: center;
          color: #FFFFFF;
        }}
        .logo-img {{
          width: 64px;
          height: 64px;
          border-radius: 50%;
          object-fit: cover;
          border: 2.5px solid #E8C39E;
          background-color: #FFFDF8;
          box-shadow: 0 6px 16px rgba(0, 0, 0, 0.25);
          display: block;
          margin: 0 auto 14px auto;
        }}
        .brand-title {{
          margin: 0;
          font-size: 26px;
          font-weight: 700;
          letter-spacing: -0.4px;
          color: #FFFFFF;
        }}
        .brand-sub {{
          margin: 6px 0 0 0;
          font-size: 11px;
          text-transform: uppercase;
          letter-spacing: 2.5px;
          color: #E8C39E;
          font-weight: 600;
        }}
        .body-card {{
          padding: 36px 32px;
        }}
        .status-pill {{
          display: inline-block;
          background-color: #E8F5F1;
          color: #0E776C;
          font-weight: 700;
          font-size: 11px;
          padding: 5px 14px;
          border-radius: 20px;
          text-transform: uppercase;
          letter-spacing: 1.2px;
          border: 1px solid #B8E2D8;
          margin-bottom: 18px;
        }}
        .greeting {{
          color: #114B5F;
          font-size: 24px;
          font-weight: 700;
          margin: 0 0 12px 0;
          letter-spacing: -0.3px;
        }}
        .intro-text {{
          font-size: 15px;
          line-height: 1.65;
          color: #4A5568;
          margin: 0 0 24px 0;
        }}
        .ticket-box {{
          background: #FAF8F3;
          border: 1px solid #E6DEC9;
          border-radius: 14px;
          padding: 22px 24px;
          margin: 24px 0;
          position: relative;
        }}
        .ticket-ref {{
          padding-bottom: 16px;
          margin-bottom: 16px;
          border-bottom: 1px dashed #D6CDBC;
        }}
        .ref-label {{
          font-size: 11px;
          text-transform: uppercase;
          letter-spacing: 1.8px;
          color: #839788;
          font-weight: 700;
          margin-bottom: 4px;
        }}
        .ref-val {{
          font-size: 24px;
          font-family: 'SF Mono', Menlo, Consolas, Monaco, monospace;
          font-weight: 800;
          color: #114B5F;
          letter-spacing: 1px;
        }}
        .info-table {{
          width: 100%;
          border-collapse: collapse;
        }}
        .info-table td {{
          padding: 8px 0;
          font-size: 14px;
          vertical-align: top;
        }}
        .info-lbl {{
          width: 38%;
          color: #52706B;
          font-weight: 600;
        }}
        .info-val {{
          color: #1A202C;
          font-weight: 700;
        }}
        .meet-card {{
          background: linear-gradient(135deg, #F0F8F6 0%, #E5F3EF 100%);
          border: 1.5px solid #9FD3C7;
          border-radius: 14px;
          padding: 26px 22px;
          margin: 28px 0;
          text-align: center;
        }}
        .meet-title {{
          margin: 0 0 8px 0;
          font-size: 16px;
          font-weight: 700;
          color: #114B5F;
        }}
        .meet-subtitle {{
          margin: 0 0 18px 0;
          font-size: 13px;
          color: #52706B;
        }}
        .cta-btn {{
          display: inline-block;
          background: linear-gradient(135deg, #0E776C 0%, #114B5F 100%);
          color: #FFFFFF !important;
          font-weight: 700;
          font-size: 15px;
          text-decoration: none;
          padding: 14px 34px;
          border-radius: 30px;
          box-shadow: 0 5px 15px rgba(14, 119, 108, 0.35);
          letter-spacing: 0.2px;
        }}
        .meet-url {{
          display: block;
          margin-top: 14px;
          font-size: 12px;
          color: #0E776C;
          word-break: break-all;
          text-decoration: underline;
        }}
        .guidance-box {{
          background-color: #FDFBF7;
          border-left: 4px solid #D4A373;
          border-radius: 0 12px 12px 0;
          padding: 18px 20px;
          margin-top: 26px;
        }}
        .guidance-title {{
          margin: 0 0 8px 0;
          font-size: 13px;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 1px;
          color: #8C6239;
        }}
        .guidance-list {{
          margin: 0;
          padding-left: 18px;
          font-size: 13px;
          line-height: 1.65;
          color: #5A6268;
        }}
        .footer {{
          background-color: #FAF8F2;
          padding: 26px 32px;
          text-align: center;
          font-size: 12px;
          line-height: 1.6;
          color: #839788;
          border-top: 1px solid #E8E1D0;
        }}
        .footer strong {{
          color: #164D59;
        }}
      </style>
    </head>
    <body>
      <div class="wrapper">
        <div class="top-gold-bar"></div>
        <div class="header">
          <img src="{AMEYA_LOGO_URL}" alt="Ameya Consultancy Logo" class="logo-img" />
          <h1 class="brand-title">Ameya Consultancy</h1>
          <p class="brand-sub">Her Health Connect · Dr. Nisha Ghelani, MD (Ob & Gyn)</p>
        </div>
        <div class="body-card">
          <span class="status-pill">✓ Appointment Confirmed</span>
          <h2 class="greeting">Hello {patient_name},</h2>
          <p class="intro-text">
            Your appointment with <strong>Dr. Nisha Ghelani</strong>, MD (Ob & Gyn) is confirmed.
            An interactive calendar invitation (<code>.ics</code>) is attached below so you can sync this to your Google or Apple Calendar in one click.
          </p>
          
          <div class="ticket-box">
            <div class="ticket-ref">
              <div class="ref-label">Official Booking Reference</div>
              <div class="ref-val">{reference}</div>
            </div>
            <table class="info-table">
              <tr>
                <td class="info-lbl">Consultation Format:</td>
                <td class="info-val">{type_label}</td>
              </tr>
              <tr>
                <td class="info-lbl">Clinical Pathway:</td>
                <td class="info-val">{focus_area}</td>
              </tr>
              <tr>
                <td class="info-lbl">Scheduled Date:</td>
                <td class="info-val">{preferred_date}</td>
              </tr>
              <tr>
                <td class="info-lbl">Scheduled Time:</td>
                <td class="info-val">{preferred_time} (India Standard Time)</td>
              </tr>
            </table>
            <p style="margin: 12px 0 0 0; font-size: 12px; color: #839788; font-style: italic;">
              * The attached calendar invite automatically converts this consultation to your local timezone upon opening.
            </p>
          </div>

          {f'''
          <div class="meet-card">
            <div class="meet-title">Private Video Consultation Room</div>
            <div class="meet-subtitle">High-definition, encrypted video powered by Google Meet</div>
            <a href="{meeting_url}" class="cta-btn">Join Google Meet</a>
            <a href="{meeting_url}" class="meet-url">{meeting_url}</a>
            <p style="margin: 14px 0 0 0; font-size: 12px; color: #52706B;">
              🔒 No app download necessary. Simply tap the button above when your appointment begins.
            </p>
          </div>
          ''' if is_virtual and meeting_url else f'''
          <div style="margin: 24px 0; padding: 20px; background: #FAF8F2; border-radius: 12px; border: 1px solid #E5DEC9;">
            <p style="margin: 0; font-weight: bold; color: #164D59; font-size: 15px;">🏥 Clinic Location:</p>
            <p style="margin: 6px 0 0 0; color: #52706B; font-size: 14px; line-height: 1.5;">{CLINIC_ADDRESS}</p>
          </div>
          '''}

          <div class="guidance-box">
            <div class="guidance-title">📋 Preparation For Your Consultation</div>
            <ol class="guidance-list">
              <li><strong>Quiet Space:</strong> Choose a well-lit, private room where you feel relaxed.</li>
              <li><strong>Medical History:</strong> Keep any previous prescriptions, scans, or symptom timelines accessible.</li>
              <li><strong>Questions:</strong> Note down your primary questions so Dr. Nisha can address each one thoroughly.</li>
            </ol>
          </div>

          <p style="margin-top: 28px; font-size: 13px; color: #839788; text-align: center;">
            Need help or have questions? Contact Dr. Nisha directly at <strong>{CLINIC_PHONE}</strong> or reply to this email.
          </p>
        </div>
        <div class="footer">
          <strong>Ameya Consultancy · Dr. Nisha Ghelani, MD (Ob & Gyn)</strong><br>
          Private women's health consultation · 22+ Years Clinical Excellence<br>
          <span style="font-size: 11px; color: #A0AEC0; margin-top: 6px; display: inline-block;">
            Confidential medical communication intended exclusively for {patient_name}.
          </span>
        </div>
      </div>
    </body>
    </html>
    """

    # 2. Render Doctor HTML email (doctor clinical alert voice with reports & patient dossier)
    reports_html = ""
    if attachment_filenames:
        reports_cards = "".join(f"""
        <div style="background: #FFFFFF; border: 1px solid #C4E2DC; border-radius: 8px; padding: 10px 14px; margin: 6px 0; font-size: 13px; color: #164D59; display: flex; align-items: center; justify-content: space-between;">
          <span>📄 <strong>{fn}</strong></span>
          <span style="font-size: 11px; background: #EAF2F1; color: #0E776C; padding: 2px 8px; border-radius: 10px; font-weight: bold;">Attached</span>
        </div>
        """ for fn in attachment_filenames)
        reports_html = f"""
        <div style="margin-top: 20px; padding: 18px; background: #F0F8F6; border-radius: 12px; border: 1px solid #B8E2D8;">
          <div style="font-weight: 700; color: #0E776C; font-size: 13px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;">
            📎 Uploaded Medical Reports & Scans ({len(attachment_filenames)}):
          </div>
          {reports_cards}
          <p style="margin: 10px 0 0 0; font-size: 12px; color: #0E776C; font-weight: 600;">
            ✓ All patient files are attached directly to this email for your immediate review.
          </p>
        </div>
        """
    else:
        reports_html = """
        <div style="margin-top: 14px; font-size: 13px; color: #839788;">
          <span style="font-weight: bold; color: #52706B;">Uploaded Reports:</span> None uploaded by patient
        </div>
        """

    doctor_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>New Consultation Dossier - Dr. Nisha Ghelani</title>
      <style>
        body {{
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
          background-color: #F6F4EF;
          margin: 0;
          padding: 24px 12px;
          color: #2B2D42;
          -webkit-font-smoothing: antialiased;
        }}
        .wrapper {{
          max-width: 600px;
          margin: 0 auto;
          background: #FFFFFF;
          border-radius: 18px;
          overflow: hidden;
          border: 1px solid #E5DEC9;
          box-shadow: 0 10px 35px rgba(22, 77, 89, 0.08);
        }}
        .top-gold-bar {{
          height: 5px;
          background: linear-gradient(90deg, #D4A373 0%, #E8C39E 50%, #D4A373 100%);
        }}
        .header {{
          background: linear-gradient(135deg, #0F3E4D 0%, #164D59 55%, #114B5F 100%);
          padding: 34px 24px 30px;
          text-align: center;
          color: #FFFFFF;
        }}
        .logo-img {{
          width: 64px;
          height: 64px;
          border-radius: 50%;
          object-fit: cover;
          border: 2.5px solid #E8C39E;
          background-color: #FFFDF8;
          box-shadow: 0 6px 16px rgba(0, 0, 0, 0.25);
          display: block;
          margin: 0 auto 14px auto;
        }}
        .brand-title {{
          margin: 0;
          font-size: 26px;
          font-weight: 700;
          letter-spacing: -0.4px;
          color: #FFFFFF;
        }}
        .brand-sub {{
          margin: 6px 0 0 0;
          font-size: 11px;
          text-transform: uppercase;
          letter-spacing: 2.5px;
          color: #E8C39E;
          font-weight: 600;
        }}
        .body-card {{
          padding: 36px 32px;
        }}
        .status-pill {{
          display: inline-block;
          background-color: #EBF3F5;
          color: #164D59;
          font-weight: 700;
          font-size: 11px;
          padding: 5px 14px;
          border-radius: 20px;
          text-transform: uppercase;
          letter-spacing: 1.2px;
          border: 1px solid #BCD1D6;
          margin-bottom: 18px;
        }}
        .greeting {{
          color: #114B5F;
          font-size: 24px;
          font-weight: 700;
          margin: 0 0 12px 0;
          letter-spacing: -0.3px;
        }}
        .intro-text {{
          font-size: 15px;
          line-height: 1.65;
          color: #4A5568;
          margin: 0 0 24px 0;
        }}
        .ticket-box {{
          background: #FAF8F3;
          border: 1px solid #E6DEC9;
          border-radius: 14px;
          padding: 22px 24px;
          margin: 24px 0;
        }}
        .ticket-ref {{
          padding-bottom: 16px;
          margin-bottom: 16px;
          border-bottom: 1px dashed #D6CDBC;
        }}
        .ref-label {{
          font-size: 11px;
          text-transform: uppercase;
          letter-spacing: 1.8px;
          color: #839788;
          font-weight: 700;
          margin-bottom: 4px;
        }}
        .ref-val {{
          font-size: 24px;
          font-family: 'SF Mono', Menlo, Consolas, Monaco, monospace;
          font-weight: 800;
          color: #114B5F;
          letter-spacing: 1px;
        }}
        .dossier-table {{
          width: 100%;
          border-collapse: collapse;
        }}
        .dossier-table td {{
          padding: 9px 0;
          font-size: 14px;
          border-bottom: 1px solid #F0ECE1;
          vertical-align: top;
        }}
        .dossier-table tr:last-child td {{
          border-bottom: none;
        }}
        .dossier-lbl {{
          width: 36%;
          color: #52706B;
          font-weight: 600;
        }}
        .dossier-val {{
          color: #1A202C;
          font-weight: 700;
        }}
        .notes-card {{
          background-color: #FAF8F2;
          border-left: 4px solid #164D59;
          border-radius: 0 10px 10px 0;
          padding: 16px 18px;
          margin: 20px 0;
        }}
        .notes-lbl {{
          font-size: 12px;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 1px;
          color: #164D59;
          margin-bottom: 6px;
        }}
        .notes-val {{
          font-size: 14px;
          color: #2D3748;
          line-height: 1.55;
        }}
        .meet-card {{
          background: linear-gradient(135deg, #F0F8F6 0%, #E5F3EF 100%);
          border: 1.5px solid #9FD3C7;
          border-radius: 14px;
          padding: 24px 20px;
          margin: 26px 0;
          text-align: center;
        }}
        .meet-title {{
          margin: 0 0 6px 0;
          font-size: 16px;
          font-weight: 700;
          color: #114B5F;
        }}
        .cta-btn {{
          display: inline-block;
          background: linear-gradient(135deg, #0E776C 0%, #114B5F 100%);
          color: #FFFFFF !important;
          font-weight: 700;
          font-size: 15px;
          text-decoration: none;
          padding: 14px 34px;
          border-radius: 30px;
          box-shadow: 0 5px 15px rgba(14, 119, 108, 0.35);
          letter-spacing: 0.2px;
          margin: 12px 0 8px 0;
        }}
        .meet-url {{
          display: block;
          font-size: 12px;
          color: #0E776C;
          word-break: break-all;
          text-decoration: underline;
        }}
        .footer {{
          background-color: #FAF8F2;
          padding: 24px 32px;
          text-align: center;
          font-size: 12px;
          line-height: 1.6;
          color: #839788;
          border-top: 1px solid #E8E1D0;
        }}
      </style>
    </head>
    <body>
      <div class="wrapper">
        <div class="top-gold-bar"></div>
        <div class="header">
          <img src="{AMEYA_LOGO_URL}" alt="Ameya Consultancy Logo" class="logo-img" />
          <h1 class="brand-title">Ameya Consultancy</h1>
          <p class="brand-sub">Clinical Dossier & Appointment Alert · Dr. Nisha Ghelani</p>
        </div>
        <div class="body-card">
          <span class="status-pill">⚡ New Booking Received</span>
          <h2 class="greeting">Hello Dr. Nisha,</h2>
          <p class="intro-text">
            A new consultation has been booked on the Ameya Consultancy portal. All patient details and clinical intake information are summarized below.
          </p>
          
          <div class="ticket-box">
            <div class="ticket-ref">
              <div class="ref-label">Booking Reference</div>
              <div class="ref-val">{reference}</div>
            </div>
            <table class="dossier-table">
              <tr>
                <td class="dossier-lbl">Patient Full Name:</td>
                <td class="dossier-val">{patient_name}</td>
              </tr>
              <tr>
                <td class="dossier-lbl">Contact Phone:</td>
                <td class="dossier-val">
                  <a href="tel:{patient_phone}" style="color: #0E776C; text-decoration: none; font-weight: bold;">{patient_phone}</a>
                  {f' · <a href="{wa_patient_link}" style="color: #25D366; text-decoration: none; font-weight: bold;">WhatsApp</a>' if wa_patient_link else ''}
                </td>
              </tr>
              <tr>
                <td class="dossier-lbl">Contact Email:</td>
                <td class="dossier-val"><a href="mailto:{patient_email}" style="color: #0E776C; text-decoration: none;">{patient_email}</a></td>
              </tr>
              <tr>
                <td class="dossier-lbl">Care Focus:</td>
                <td class="dossier-val"><span style="background: #E8F5F1; color: #0E776C; padding: 3px 8px; border-radius: 8px; font-size: 13px;">{focus_area}</span></td>
              </tr>
              <tr>
                <td class="dossier-lbl">Consultation Date:</td>
                <td class="dossier-val">{preferred_date}</td>
              </tr>
              <tr>
                <td class="dossier-lbl">Consultation Time:</td>
                <td class="dossier-val">{preferred_time} (IST)</td>
              </tr>
            </table>
          </div>

          <div class="notes-card">
            <div class="notes-lbl">Patient Notes / Health Concern:</div>
            <div class="notes-val">"{notes if notes else 'No specific concerns noted in request.'}"</div>
          </div>

          {reports_html}

          {f'''
          <div class="meet-card">
            <div class="meet-title">Scheduled Google Meet Room</div>
            <div style="font-size: 12px; color: #0E776C; font-weight: 600; margin-bottom: 6px;">
              ✓ Synced automatically to your Google Calendar
            </div>
            <a href="{meeting_url}" class="cta-btn">Start / Join Consultation</a>
            <a href="{meeting_url}" class="meet-url">{meeting_url}</a>
          </div>
          ''' if is_virtual and meeting_url else ''}
        </div>
        <div class="footer">
          <strong>Ameya Consultancy Notification Engine</strong><br>
          Direct clinical alert prepared for Dr. Nisha Ghelani, MD (Ob & Gyn)<br>
          <span style="font-size: 11px; color: #A0AEC0;">
            Confidential medical record. Do not forward.
          </span>
        </div>
      </div>
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
