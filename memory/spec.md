# Ameya Consultancy — Living Spec & Architecture

Public women's health consultation website for Dr. Nisha Ghelani, MD (Ob & Gyn), 22 years of experience. Visitors can explore care pathways, weekly availability, FAQs, and submit a consultation request. Requests are saved to MongoDB through `POST /api/appointments`, validated for Tuesday/Thursday/Saturday availability, and confirmed with an AMY reference.

## Current Setup & Configuration
- **Doctor Testing Email**: Currently set to `dirgh8011patel@gmail.com` via `DOCTOR_EMAIL` environment variable fallback.
- **Production Doctor Target Email**: `nishaghelani78@gmail.com`.
- **Google Calendar API Integration**: Configured with OAuth2 refresh token to dynamically create events and genuine Google Meet rooms (`meet.google.com/xxx-yyyy-zzz`).
- **Resend Email Service**: Configured with `RESEND_API_KEY`. Sends patient confirmation voice to patient and doctor alert voice (with uploaded medical report attachments) to the doctor.

## Transition Checklist to Dr. Nisha Ghelani's Email
When ready to transfer live notifications to Dr. Nisha:
1. **Google Calendar API**:
   - In Google Cloud Console (`Ameya Consultancy` project), under OAuth Consent Screen -> Test Users, add `nishaghelani78@gmail.com`.
   - Authorize `Google Calendar API` via Google OAuth Playground using Dr. Nisha's Google account to obtain her `GOOGLE_REFRESH_TOKEN`.
   - Update `GOOGLE_REFRESH_TOKEN` on Vercel:
     `vercel env add GOOGLE_REFRESH_TOKEN production`
2. **Doctor Email Environment Variable**:
   - Update `DOCTOR_EMAIL` on Vercel to Dr. Nisha's email:
     `printf "nishaghelani78@gmail.com" | vercel env add DOCTOR_EMAIL production --yes`
3. **Resend Domain Verification (to deliver to patients & Dr. Nisha)**:
   - Add domain `ameyaconsultancy.com` to Resend (`resend.com/domains`) and add the 3 DNS records (DKIM/SPF).
   - Set `RESEND_FROM_EMAIL="Ameya Consultancy <consultation@ameyaconsultancy.com>"` on Vercel.
   - Alternatively: use Gmail App Password for `nishaghelani78@gmail.com` (`SMTP_USER` & `SMTP_PASSWORD`).