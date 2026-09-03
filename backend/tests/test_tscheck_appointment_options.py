"""Criterion: Availability is only inside booking.

GET /api/appointments/options returns nine server-anchored dates on
Tuesday, Thursday, or Saturday in Asia/Kolkata.
"""

ALLOWED_DAYS = {"Tuesday", "Thursday", "Saturday"}


def test_booking_options_returns_nine_tue_thu_sat_dates(client):
    resp = client.get("/appointments/options")
    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert body["timezone"] == "Asia/Kolkata"
    assert set(body["available_days"]) == ALLOWED_DAYS

    dates = body["available_dates"]
    assert len(dates) == 9, f"expected 9 dates, got {len(dates)}: {dates}"
    for entry in dates:
        assert entry["day_label"] in ALLOWED_DAYS, entry
        assert "date" in entry and "display_label" in entry
