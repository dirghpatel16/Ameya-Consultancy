"""Criterion: Appointment request completes successfully.

POST /api/appointments stores a request and returns an AMY-prefixed reference.
Includes a validation-rejection case for a disallowed weekday.
"""


def _next_available_date(client) -> str:
    options = client.get("/appointments/options").json()
    return options["available_dates"][0]["date"]


def test_create_appointment_returns_amy_reference(client):
    preferred_date = _next_available_date(client)
    payload = {
        "full_name": "tscheck-appointment Jordan",
        "email": "tscheck-appointment@example.com",
        "phone": "+91 9876543210",
        "consultation_type": "video_consultation",
        "focus_area": "General wellness",
        "preferred_date": preferred_date,
        "preferred_time": "Morning preference",
        "notes": "tscheck fixture booking",
    }

    resp = client.post("/appointments", json=payload)
    assert resp.status_code == 201, resp.text
    body = resp.json()

    assert body["reference"].startswith("AMY-"), body["reference"]
    assert body["status"] == "requested"
    assert body["full_name"] == payload["full_name"]
    assert body["preferred_date"] == preferred_date


def test_create_appointment_rejects_non_available_weekday(client):
    # Pick a date guaranteed NOT to be Tue/Thu/Sat: force a Sunday/Monday-ish offset.
    import datetime

    d = datetime.date.today()
    while d.weekday() not in (0, 2, 4, 6):  # Mon, Wed, Fri, Sun -> disallowed
        d += datetime.timedelta(days=1)

    payload = {
        "full_name": "tscheck-appointment-invalid Jordan",
        "email": "tscheck-appointment-invalid@example.com",
        "phone": "+91 9876543210",
        "consultation_type": "clinic_visit",
        "focus_area": "General wellness",
        "preferred_date": d.isoformat(),
        "preferred_time": "Afternoon preference",
        "notes": "",
    }

    resp = client.post("/appointments", json=payload)
    assert resp.status_code == 422, resp.text
