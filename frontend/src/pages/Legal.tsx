import { ArrowLeft, HeartHandshake } from "lucide-react";
import { Link } from "react-router-dom";

interface LegalSection {
  title: string;
  body: string;
}

function LegalPage({ kind, title, intro, sections }: { kind: "terms" | "privacy"; title: string; intro: string; sections: LegalSection[] }) {
  return (
    <main className="min-h-screen bg-[#F4F1E8] px-5 py-10 text-[#263D3A] sm:px-8 lg:py-16" data-testid={`${kind}-page`}>
      <div className="mx-auto max-w-3xl">
        <Link to="/" className="inline-flex min-h-11 items-center gap-2 text-sm font-semibold text-[#0E776C] hover:text-[#E07A5F]" data-testid={`${kind}-back-link`}><ArrowLeft className="size-4" /> Back to Ameya Consultancy</Link>
        <header className="mt-10 border-b border-[#D9DFD4] pb-10" data-testid={`${kind}-header`}>
          <div className="flex items-center gap-3 text-[#0E776C]"><HeartHandshake className="size-6" /><span className="text-xs font-bold uppercase tracking-[0.18em]">Her Health Connect</span></div>
          <h1 className="mt-7 font-serif text-5xl leading-tight text-[#164D59] sm:text-6xl" data-testid={`${kind}-heading`}>{title}</h1>
          <p className="mt-6 max-w-2xl text-base leading-relaxed text-[#52706B]" data-testid={`${kind}-intro`}>{intro}</p>
          <p className="mt-4 text-xs font-semibold uppercase tracking-[0.12em] text-[#839788]" data-testid={`${kind}-updated`}>Last updated September 2026</p>
        </header>
        <div className="space-y-10 py-10" data-testid={`${kind}-content`}>{sections.map((section, index) => <section key={section.title} data-testid={`${kind}-section-${index + 1}`}><h2 className="font-serif text-2xl text-[#164D59]">{section.title}</h2><p className="mt-3 whitespace-pre-line text-sm leading-7 text-[#52706B]">{section.body}</p></section>)}</div>
        <div className="border-t border-[#D9DFD4] pt-7 text-sm text-[#52706B]" data-testid={`${kind}-contact`}>Questions? Email <a href="mailto:nishaghelani78@gmail.com" className="font-semibold text-[#0E776C] underline">nishaghelani78@gmail.com</a>.</div>
      </div>
    </main>
  );
}

export function TermsPage() {
  return <LegalPage kind="terms" title="Terms & Conditions" intro="These terms explain how Ameya Consultancy's informational website and appointment service may be used." sections={[
    { title: "Medical scope", body: "Website content is general health information and does not replace a diagnosis, examination, prescription, or emergency care. A consultation relationship begins only when Dr. Nisha accepts and conducts an appointment." },
    { title: "Appointments", body: "Submitted dates and times are preferences until confirmed. Availability may change. Google Meet links are created only when Calendar integration is active; otherwise the practice will follow up directly." },
    { title: "Your responsibilities", body: "Provide accurate contact and health information, join from a private and safe location, and do not use this service for emergencies. You are responsible for ensuring uploaded reports belong to you or that you have permission to share them." },
    { title: "Files and technology", body: "Only PDF, JPG, and PNG reports up to 10 MB each are accepted. Internet, device, Google Meet, WhatsApp, or third-party service interruptions may affect access and are outside the practice's direct control." },
    { title: "Urgent care", body: "Ameya Consultancy is not an emergency service. For severe pain, heavy bleeding, breathing difficulty, loss of consciousness, or an obstetric emergency, contact the nearest emergency department immediately." },
    { title: "Changes", body: "These terms may be updated as the consultation service evolves. Continued use after an update means you accept the revised terms." },
  ]} />;
}

export function PrivacyPage() {
  return <LegalPage kind="privacy" title="Privacy Policy" intro="This policy describes the personal and health-related information collected when you use Ameya Consultancy's website and appointment service." sections={[
    { title: "Information collected", body: "We collect the name, email, phone number, care pathway, preferred appointment date and time, optional notes, and any PDF/JPG/PNG reports you choose to attach." },
    { title: "How information is used", body: "Information is used to arrange and deliver the consultation, contact you about timing, prepare for the discussion, maintain a booking record, and create a Google Meet event when the integration is active." },
    { title: "Storage and access", body: "Appointment details and attachments are stored with restricted operational access. Reports are not used for advertising. Reasonable security safeguards are applied, but no internet transmission can be guaranteed completely secure." },
    { title: "External services", body: "WhatsApp links open Meta's service and are governed by WhatsApp's privacy terms. When activated, Google Calendar and Google Meet process appointment information under Google's terms. No Meet data is sent while the integration is disconnected." },
    { title: "Retention and deletion", body: "Information is retained only as long as reasonably needed for consultation coordination, clinical follow-up, legal obligations, and dispute resolution. You may contact the practice to request access, correction, or deletion where applicable." },
    { title: "Consent", body: "By submitting an appointment, you consent to the stated collection and use of your information. Attaching a report is optional." },
  ]} />;
}