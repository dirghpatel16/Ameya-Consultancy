# Ameya Consultancy — Living Spec

## Purpose
Public consultation website for Ameya Consultancy / Her Health Connect, a solo women's health practice led by Dr. Nisha Ghelani, MD (Ob & Gyn), with 22 years of experience.

## Core flow
- The visual experience uses a Maven-inspired editorial rhythm without copying its branding: announcement strip, floating white navigation, full-bleed photo hero, colorful care cards, and alternating campaign-like content blocks.
- Visitors learn about Dr. Nisha's philosophy and care pathways.
- The care pathway tabs cover antenatal care, postnatal recovery, puberty/adolescent health, menopause, and expert report opinion.
- Visitors request a consultation through an on-site form. Eligible days are Tuesday, Thursday, and Saturday; Monday, Wednesday, Friday, and Sunday are closed.
- The backend stores a request in MongoDB and returns a generated AMY reference. The frontend shows an immediate confirmation dialog with contact fallback details.
- The mobile viewport has a fixed call/book quick-action bar; booking opens in a bottom-sheet style dialog.

## Data model
`AppointmentCreate`: full_name, email, phone, consultation_type, focus_area, preferred_date, preferred_time, notes.
`Appointment`: request fields plus id, reference, status (`requested`), created_at.

## Auth
No authentication. The public site has no gated areas or seeded accounts.

## Contact
Phone: +91 6355734167. Email: nishaghelani78@gmail.com.