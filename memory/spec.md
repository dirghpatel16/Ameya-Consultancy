# Ameya Consultancy — Living Spec & Architecture

Public women's health consultation website for Dr. Nisha Ghelani, MD (Ob & Gyn), 22 years of experience. Visitors can explore care pathways, weekly availability, FAQs, and submit a consultation request. Requests are saved to MongoDB through `POST /api/appointments`, validated for Tuesday/Thursday/Saturday availability, and confirmed with an AMY reference.

## Current Setup & Configuration
- **Doctor Production Email**: Set to Dr. Nisha Ghelani (`nishaghelani78@gmail.com`) in `email_service.py` and via `DOCTOR_EMAIL` environment variable.
- **Google Calendar API Integration**: Fully connected to Dr. Nisha's Google Account (`nishaghelani78@gmail.com`) with OAuth2 client `246377409601-j2kr12i8fgjuguhu9tibkoodm9kf4e13.apps.googleusercontent.com` and `GOOGLE_REFRESH_TOKEN`. Dynamically creates calendar events and live Google Meet links on Dr. Nisha's calendar.
- **Resend Email Service**: Configured with `RESEND_API_KEY` and official sender `Ameya Consultancy <appointments@ameyaconsultancy.com>`. Sends patient confirmation voice to patient and doctor alert voice (with uploaded medical report attachments) to Dr. Nisha.