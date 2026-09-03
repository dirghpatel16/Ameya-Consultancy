import datetime
import json
import logging
import os
import ssl
import urllib.error
import urllib.parse
import urllib.request

logger = logging.getLogger("ameya.calendar")

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_CALENDAR_EVENTS_URL = "https://www.googleapis.com/calendar/v3/calendars/primary/events?conferenceDataVersion=1"


def _get_ssl_context():
    try:
        return ssl.create_default_context()
    except Exception:
        return ssl._create_unverified_context()


def get_google_access_token() -> str | None:
    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
    refresh_token = os.environ.get("GOOGLE_REFRESH_TOKEN")

    if not (client_id and client_secret and refresh_token):
        logger.info("Google Calendar credentials not fully configured in environment.")
        return None

    data = urllib.parse.urlencode({
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }).encode("utf-8")

    req = urllib.request.Request(
        GOOGLE_TOKEN_URL,
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded", "User-Agent": "AmeyaConsultancy/1.0"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=10, context=_get_ssl_context()) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return body.get("access_token")
    except urllib.error.URLError:
        try:
            with urllib.request.urlopen(req, timeout=10, context=ssl._create_unverified_context()) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                return body.get("access_token")
        except Exception as exc:
            logger.error("Failed to fetch Google access token (unverified fallback): %s", exc)
            return None
    except Exception as exc:
        logger.error("Failed to fetch Google access token: %s", exc)
        return None


def parse_slot_to_iso(date_str: str, time_str: str, duration_mins: int = 45) -> tuple[str, str]:
    parts = time_str.strip().split()
    time_part = parts[0]
    meridiem = parts[1].upper() if len(parts) > 1 else "AM"
    h_str, m_str = time_part.split(":")
    hour = int(h_str)
    minute = int(m_str)
    if meridiem == "PM" and hour != 12:
        hour += 12
    elif meridiem == "AM" and hour == 12:
        hour = 0
    start_dt = datetime.datetime.strptime(f"{date_str} {hour:02d}:{minute:02d}", "%Y-%m-%d %H:%M")
    end_dt = start_dt + datetime.timedelta(minutes=duration_mins)
    return start_dt.strftime("%Y-%m-%dT%H:%M:00+05:30"), end_dt.strftime("%Y-%m-%dT%H:%M:00+05:30")


def create_calendar_event_with_meet(
    patient_name: str,
    patient_email: str,
    patient_phone: str,
    preferred_date: str,
    preferred_time: str,
    focus_area: str,
    reference: str,
    notes: str = "",
) -> tuple[str | None, str | None]:
    """
    Creates an event in Dr. Nisha / Dirgh's Google Calendar with a real, live Google Meet link.
    Returns (meeting_url, event_html_link).
    """
    token = get_google_access_token()
    if not token:
        logger.warning("No Google access token available, skipping Calendar API event creation.")
        return None, None

    try:
        start_iso, end_iso = parse_slot_to_iso(preferred_date, preferred_time)
    except Exception as exc:
        logger.error("Failed to parse appointment time for Google Calendar: %s", exc)
        return None, None

    summary = f"Ameya: {focus_area.replace('_', ' ').title()} Consultation — {patient_name} ({reference})"
    description = (
        f"Ameya Consultancy — Women's Health Consultation\n"
        f"Doctor: Dr. Nisha Ghelani, MD (Ob & Gyn)\n"
        f"Patient: {patient_name}\n"
        f"Email: {patient_email}\n"
        f"Phone: {patient_phone}\n"
        f"Reference: {reference}\n"
        f"Care Pathway: {focus_area}\n"
    )
    if notes:
        description += f"Notes: {notes}\n"

    event_body = {
        "summary": summary,
        "description": description,
        "start": {"dateTime": start_iso, "timeZone": "Asia/Kolkata"},
        "end": {"dateTime": end_iso, "timeZone": "Asia/Kolkata"},
        "attendees": [
            {"email": patient_email, "displayName": patient_name},
        ],
        "conferenceData": {
            "createRequest": {
                "requestId": f"meet-{reference.lower()}",
                "conferenceSolutionKey": {"type": "hangoutsMeet"},
            }
        },
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "email", "minutes": 24 * 60},
                {"method": "popup", "minutes": 30},
            ],
        },
    }

    req = urllib.request.Request(
        GOOGLE_CALENDAR_EVENTS_URL,
        data=json.dumps(event_body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "AmeyaConsultancy/1.0",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=12, context=_get_ssl_context()) as resp:
            event = json.loads(resp.read().decode("utf-8"))
            html_link = event.get("htmlLink")
            meet_uri = None
            conference_data = event.get("conferenceData", {})
            entry_points = conference_data.get("entryPoints", [])
            for ep in entry_points:
                if ep.get("entryPointType") == "video" or "meet.google.com" in ep.get("uri", ""):
                    meet_uri = ep.get("uri")
                    break
            logger.info("Successfully created Google Calendar event %s with Meet link: %s", html_link, meet_uri)
            return meet_uri, html_link
    except urllib.error.URLError:
        try:
            with urllib.request.urlopen(req, timeout=12, context=ssl._create_unverified_context()) as resp:
                event = json.loads(resp.read().decode("utf-8"))
                html_link = event.get("htmlLink")
                meet_uri = None
                for ep in event.get("conferenceData", {}).get("entryPoints", []):
                    if ep.get("entryPointType") == "video" or "meet.google.com" in ep.get("uri", ""):
                        meet_uri = ep.get("uri")
                        break
                logger.info("Successfully created Google Calendar event (unverified SSL) with Meet: %s", meet_uri)
                return meet_uri, html_link
        except Exception as exc:
            logger.error("Google Calendar API event creation failed (fallback): %s", exc)
            return None, None
    except Exception as exc:
        logger.error("Google Calendar API event creation failed: %s", exc)
        return None, None
