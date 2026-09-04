# Ameya Consultancy — Living Spec & Architecture

Public women's health consultation website for Dr. Nisha Ghelani, MD (Ob & Gyn), 22 years of experience. Visitors can explore care pathways, weekly availability, FAQs, and submit a consultation request. Requests are saved to MongoDB through `POST /api/appointments`, validated for Tuesday/Thursday/Saturday availability, and confirmed with an AMY reference.

## Current Setup & Configuration
- **Doctor Production Email**: Set to Dr. Nisha Ghelani (`nishaghelani78@gmail.com`) in `email_service.py` and via `DOCTOR_EMAIL` environment variable.
- **Google Calendar API Integration**: Fully connected to Dr. Nisha's Google Account (`nishaghelani78@gmail.com`) with OAuth2 client `246377409601-j2kr12i8fgjuguhu9tibkoodm9kf4e13.apps.googleusercontent.com` and `GOOGLE_REFRESH_TOKEN`. Dynamically creates calendar events and live Google Meet links on Dr. Nisha's calendar.
- **Resend Email Service**: Configured with `RESEND_API_KEY` and official sender `Ameya Consultancy <appointments@ameyaconsultancy.com>`. Sends patient confirmation email to patient and doctor alert email (with uploaded medical report attachments) to Dr. Nisha.
- **Razorpay Online Payment (Upfront ₹1,000)**:
  - Configured with `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, and `CONSULTATION_FEE_INR=1000`.
  - Backend creates Razorpay order (`POST /api/appointments/create-order`) and verifies HMAC-SHA256 signature (`POST /api/appointments`).
  - No appointment is created or calendar invite generated without verified upfront payment.
  - Payment details (Amount, Reference, Payment ID) included in patient & doctor confirmation emails.
- **Double Booking Prevention**:
  - `GET /api/appointments/options` returns `booked_slots` map by date.
  - Time slots already booked are disabled with visual "Booked" strike-through badges in the booking UI.
  - MongoDB Atlas unique compound index `preferred_date_1_preferred_time_1` on `appointments` collection prevents race conditions and duplicate bookings with atomic 409 Conflict.