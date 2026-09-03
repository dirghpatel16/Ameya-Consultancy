# Ameya Consultancy — Living Spec

## Purpose
Public consultation website for Ameya Consultancy / Her Health Connect, a solo women's health practice led by Dr. Nisha Ghelani, MD (Ob & Gyn), with 20+ years of experience.

## Core flow
- The visual experience uses a Maven-inspired editorial rhythm without copying its branding: announcement strip, floating white navigation, a split art-directed hero, colorful care cards, and alternating campaign-like content blocks.
- The hero's primary promise is “Care for every stage of womanhood,” supported by a restrained editorial collage, an identity-matched Dr. Nisha portrait, calm motion, a stage card, a 20+ year trust card, and direct booking CTA.
- Visitors learn about Dr. Nisha's philosophy and care pathways.
- The care pathway tabs cover antenatal care, postnatal recovery, puberty/adolescent health, menopause, and expert report opinion.
- Booking is never embedded in a page section. Header, hero, pathway, CTA, footer, and mobile Book actions open one responsive appointment dialog.
- The dialog provides a calendar month view with server-anchored Tuesday/Thursday/Saturday dates and exact hourly times from 10:00 AM through 6:00 PM India time.
- Patients can attach up to three private PDF/JPG/PNG reports, maximum 10 MB each. Attachments are stored in MongoDB and linked to the appointment.
- The backend stores the appointment and returns an AMY reference plus Google Meet status. Until Calendar OAuth is connected, meeting status is `pending_connection` and no fake link is shown.
- A fixed WhatsApp button opens a prefilled chat with +91 6355734167. Mobile also retains the call/book quick-action bar.

## Data model
`AppointmentCreate`: full_name, email, phone, consultation_type, focus_area, preferred_date, preferred_time, notes, attachment_ids.
`Appointment`: request fields plus id, reference, status (`requested`), meeting_status, meeting_url, created_at.
`BookingOptions`: timezone, available_days, available_dates, available_times, google_meet_enabled.

## Auth
No authentication. The public site has no gated areas or seeded accounts.

## Contact
Phone: +91 6355734167. Email: nishaghelani78@gmail.com.

## Brand asset
The supplied gold-and-teal woman-and-leaf logo is used in the header, footer, and browser favicon.