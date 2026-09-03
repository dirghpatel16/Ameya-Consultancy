import { useState, type ChangeEvent, type FormEvent, type ReactNode } from "react";
import { useMutation } from "@tanstack/react-query";
import { motion } from "motion/react";
import {
  ArrowRight,
  ArrowUpRight,
  CalendarDays,
  Check,
  ChevronDown,
  Clock3,
  HeartHandshake,
  Mail,
  MapPin,
  Phone,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { ApiError, apiPost } from "@/lib/api";

type ConsultationType = "clinic_visit" | "video_consultation" | "second_opinion";

interface AppointmentCreate {
  full_name: string;
  email: string;
  phone: string;
  consultation_type: ConsultationType;
  focus_area: string;
  preferred_date: string;
  preferred_time: string;
  notes: string;
}

interface Appointment extends AppointmentCreate {
  id: string;
  reference: string;
  status: "requested";
  created_at: string;
}

interface BookingFormProps {
  onCreated: (appointment: Appointment) => void;
  testIdPrefix: string;
}

const focusAreas = [
  {
    id: "antenatal",
    eyebrow: "01 / Before birth",
    title: "Antenatal care",
    heading: "A steadier pregnancy, one conversation at a time.",
    body: "Trimester guidance, prenatal plans, fetal health monitoring, and the kind of unhurried counselling that makes room for every question.",
    points: ["Pregnancy journey tracking", "High-risk pregnancy guidance", "Supportive maternal counselling"],
  },
  {
    id: "postnatal",
    eyebrow: "02 / After birth",
    title: "Postnatal recovery",
    heading: "Care for the person behind the new baby.",
    body: "Thoughtful support for postpartum recovery, newborn transition, lactation, breast care, pelvic floor wellness, and emotional wellbeing.",
    points: ["Postpartum recovery review", "Lactation and breast care", "Emotional health check-in"],
  },
  {
    id: "puberty",
    eyebrow: "03 / Growing well",
    title: "Puberty & adolescent health",
    heading: "A private, respectful space to ask anything.",
    body: "Confidential guidance through hormonal shifts, menstrual health, PCOS, and body awareness—for young women and the people who support them.",
    points: ["Menstrual health and PCOS", "Confidential teen consultations", "Body awareness and education"],
  },
  {
    id: "menopause",
    eyebrow: "04 / A new rhythm",
    title: "Menopause care",
    heading: "Navigate change with clarity and confidence.",
    body: "Personalised menopause counselling, symptom relief, bone health strategies, lifestyle therapy, and thoughtful conversations around HRT.",
    points: ["Perimenopause planning", "Symptom and mood support", "Bone and lifestyle health"],
  },
  {
    id: "second_opinion",
    eyebrow: "05 / Another perspective",
    title: "Expert opinion",
    heading: "Understand your reports before you decide.",
    body: "A careful review of ultrasound scans, lab reports, surgical proposals, and complex gynaecology diagnoses, grounded in 22 years of insight.",
    points: ["Reports and checkup review", "Surgical proposal discussion", "Complex diagnosis perspective"],
  },
];

const weeklyCadence = [
  { day: "Monday", short: "MON", status: "Closed", note: "Rest day" },
  { day: "Tuesday", short: "TUE", status: "By appointment", note: "Private consultations" },
  { day: "Wednesday", short: "WED", status: "Closed", note: "Rest day" },
  { day: "Thursday", short: "THU", status: "By appointment", note: "Private consultations" },
  { day: "Friday", short: "FRI", status: "Closed", note: "Rest day" },
  { day: "Saturday", short: "SAT", status: "By appointment", note: "Private consultations" },
  { day: "Sunday", short: "SUN", status: "Closed", note: "Rest day" },
];

const faqs = [
  {
    question: "What happens after I request a consultation?",
    answer: "Your request is saved securely and a reference number is shown immediately. Dr. Nisha's team will reach out on the phone or email you provided to confirm a suitable time.",
  },
  {
    question: "Can I book a video consultation?",
    answer: "Yes. Choose Video consultation in the request form and mention anything helpful in the notes. The final appointment link and time are confirmed personally.",
  },
  {
    question: "Can I bring reports or previous prescriptions?",
    answer: "Absolutely. For an expert opinion, keep your recent reports, scans, prescriptions, and a short list of questions ready for the conversation.",
  },
  {
    question: "Is this service for urgent medical problems?",
    answer: "No. This is a planned consultation service. If you have an acute or emergency concern, please contact your nearest hospital emergency department immediately.",
  },
];

const initialForm: AppointmentCreate = {
  full_name: "",
  email: "",
  phone: "",
  consultation_type: "clinic_visit",
  focus_area: "antenatal",
  preferred_date: "",
  preferred_time: "Morning preference",
  notes: "",
};

const consultationTypes: { value: ConsultationType; label: string; detail: string }[] = [
  { value: "clinic_visit", label: "Clinic visit", detail: "In-person conversation" },
  { value: "video_consultation", label: "Video consultation", detail: "From the comfort of home" },
  { value: "second_opinion", label: "Second opinion", detail: "Review reports together" },
];

function Reveal({ children, className = "", delay = 0 }: { children: ReactNode; className?: string; delay?: number }) {
  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y: 18 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-70px" }}
      transition={{ duration: 0.65, delay, ease: [0.22, 1, 0.36, 1] }}
    >
      {children}
    </motion.div>
  );
}

function BookingForm({ onCreated, testIdPrefix }: BookingFormProps) {
  const testId = (name: string) => `${testIdPrefix}-${name}`;
  const [form, setForm] = useState<AppointmentCreate>(initialForm);
  const [dateError, setDateError] = useState("");
  const mutation = useMutation({
    mutationFn: (payload: AppointmentCreate) => apiPost<Appointment>("/appointments", payload),
    onSuccess: (appointment) => {
      toast.success("Consultation request saved", { description: `Reference ${appointment.reference}` });
      setForm(initialForm);
      setDateError("");
      onCreated(appointment);
    },
  });

  const updateField = (field: keyof AppointmentCreate) => (event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    setForm((current) => ({ ...current, [field]: event.target.value }));
    if (field === "preferred_date") setDateError("");
  };

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const selectedDate = new Date(`${form.preferred_date}T12:00:00`);
    if ([0, 1, 3, 5].includes(selectedDate.getDay())) {
      setDateError("Please choose Tuesday, Thursday, or Saturday.");
      return;
    }
    mutation.mutate(form);
  };

  const errorMessage = mutation.error instanceof ApiError && mutation.error.status === 422
    ? "Please check the date and your details, then try again."
    : mutation.error
      ? "We couldn't save that request. Please call or email the doctor directly."
      : "";

  return (
    <form onSubmit={handleSubmit} className="space-y-5" data-testid={testId("booking-form")}>
      <div className="grid gap-5 sm:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="full-name">Your name</Label>
          <Input id={`${testIdPrefix}-full-name`} required value={form.full_name} onChange={updateField("full_name")} placeholder="Full name" data-testid={testId("name-input")} />
        </div>
        <div className="space-y-2">
          <Label htmlFor="phone">Phone number</Label>
          <Input id={`${testIdPrefix}-phone`} required value={form.phone} onChange={updateField("phone")} placeholder="+91 ..." data-testid={testId("phone-input")} />
        </div>
      </div>
      <div className="space-y-2">
        <Label htmlFor="email">Email address</Label>
        <Input id={`${testIdPrefix}-email`} type="email" required value={form.email} onChange={updateField("email")} placeholder="you@example.com" data-testid={testId("email-input")} />
      </div>
      <fieldset className="space-y-3">
        <legend className="text-sm font-semibold text-[#2B2D42]">How would you like to meet?</legend>
        <div className="grid gap-2 sm:grid-cols-3">
          {consultationTypes.map((type) => (
            <button
              key={type.value}
              type="button"
              aria-pressed={form.consultation_type === type.value}
              onClick={() => setForm((current) => ({ ...current, consultation_type: type.value }))}
              className={`min-h-16 rounded-xl border px-3 py-3 text-left text-sm transition-all duration-300 hover:-translate-y-0.5 ${form.consultation_type === type.value ? "border-[#114B5F] bg-[#EAF2F1] text-[#114B5F] shadow-sm" : "border-[#E5DEC9] bg-white text-[#5C6479] hover:border-[#839788]"}`}
              data-testid={testId(`consultation-type-${type.value}`)}
            >
              <span className="block font-semibold">{type.label}</span>
              <span className="mt-1 block text-xs opacity-75">{type.detail}</span>
            </button>
          ))}
        </div>
      </fieldset>
      <div className="grid gap-5 sm:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="focus-area">What can we help with?</Label>
          <select id={`${testIdPrefix}-focus-area`} required value={form.focus_area} onChange={updateField("focus_area")} className="flex h-11 w-full rounded-lg border border-[#E5DEC9] bg-white px-3 text-sm text-[#2B2D42] outline-none ring-offset-white transition focus:border-[#114B5F] focus:ring-2 focus:ring-[#114B5F]/20" data-testid={testId("focus-select")}>
            {focusAreas.map((area) => <option key={area.id} value={area.id}>{area.title}</option>)}
          </select>
        </div>
        <div className="space-y-2">
          <Label htmlFor="preferred-date">Preferred date</Label>
          <Input id={`${testIdPrefix}-preferred-date`} type="date" required value={form.preferred_date} onChange={updateField("preferred_date")} data-testid={testId("date-input")} />
          <p className="text-xs text-[#5C6479]" data-testid={testId("date-hint")}>Tuesday, Thursday, or Saturday only.</p>
        </div>
      </div>
      {dateError && <p className="text-sm font-medium text-[#B84F3A]" role="alert" data-testid={testId("date-error")}>{dateError}</p>}
      <fieldset className="space-y-3">
        <legend className="text-sm font-semibold text-[#2B2D42]">Preferred time</legend>
        <div className="flex flex-wrap gap-2">
          {["Morning preference", "Afternoon preference", "Evening preference"].map((time) => (
            <button key={time} type="button" aria-pressed={form.preferred_time === time} onClick={() => setForm((current) => ({ ...current, preferred_time: time }))} className={`min-h-11 rounded-full border px-4 text-sm transition-all duration-300 ${form.preferred_time === time ? "border-[#114B5F] bg-[#114B5F] text-white" : "border-[#E5DEC9] bg-white text-[#5C6479] hover:border-[#114B5F]"}`} data-testid={testId(`time-${time.split(" ")[0].toLowerCase()}`)}>
              {time.replace(" preference", "")}
            </button>
          ))}
        </div>
      </fieldset>
      <div className="space-y-2">
        <Label htmlFor="notes">Anything you would like the doctor to know? <span className="font-normal text-[#5C6479]">(optional)</span></Label>
        <Textarea id={`${testIdPrefix}-notes`} value={form.notes} onChange={updateField("notes")} placeholder="A few words about what you would like to discuss..." className="min-h-24 resize-none" data-testid={testId("notes-input")} />
      </div>
      {errorMessage && <p className="text-sm font-medium text-[#B84F3A]" role="alert" data-testid={testId("form-error")}>{errorMessage}</p>}
      <Button type="submit" disabled={mutation.isPending} className="h-12 w-full rounded-full bg-[#E07A5F] text-white shadow-[0_10px_24px_rgba(224,122,95,0.22)] hover:bg-[#c9654c]" data-testid={testId("submit-button")}>
        {mutation.isPending ? "Saving your request..." : "Request a consultation"}
        {!mutation.isPending && <ArrowRight className="ml-2 size-4" />}
      </Button>
      <p className="flex items-start gap-2 text-xs leading-relaxed text-[#5C6479]" data-testid={testId("privacy-note")}><ShieldCheck className="mt-0.5 size-4 shrink-0 text-[#1A5E72]" /> Your details are used only to arrange this private consultation.</p>
    </form>
  );
}

export default function Home() {
  const [activeFocus, setActiveFocus] = useState(focusAreas[0].id);
  const [openFaq, setOpenFaq] = useState(0);
  const [mobileBookingOpen, setMobileBookingOpen] = useState(false);
  const [confirmationOpen, setConfirmationOpen] = useState(false);
  const [confirmedAppointment, setConfirmedAppointment] = useState<Appointment | null>(null);
  const activeArea = focusAreas.find((area) => area.id === activeFocus) ?? focusAreas[0];

  const scrollToBooking = () => document.getElementById("booking")?.scrollIntoView({ behavior: "smooth", block: "start" });
  const handleCreated = (appointment: Appointment) => {
    setConfirmedAppointment(appointment);
    setMobileBookingOpen(false);
    setConfirmationOpen(true);
  };

  return (
    <div className="min-h-screen overflow-x-hidden bg-white text-[#263D3A] selection:bg-[#E4B45E]/30">
      <div className="relative z-50 flex min-h-10 items-center justify-center bg-[#8FD5E1] px-5 py-2 text-center text-[11px] font-bold uppercase tracking-[0.12em] text-[#164D59] sm:text-xs" data-testid="announcement-bar"><span>Private care for every chapter of her health · Tue · Thu · Sat</span></div>
      <header className="absolute inset-x-0 top-10 z-40 border-0 bg-transparent px-4 py-3 sm:px-6 lg:px-10" data-testid="site-header">
        <div className="mx-auto flex h-[4.5rem] max-w-7xl items-center justify-between rounded-sm bg-white px-5 shadow-[0_12px_35px_rgba(23,60,58,0.12)] sm:px-8 lg:px-6">
          <a href="#top" className="group flex items-center gap-3" data-testid="brand-home-link">
            <span className="flex size-9 items-center justify-center rounded-full bg-[#0E776C] text-white transition-transform duration-300 group-hover:rotate-6"><HeartHandshake className="size-4" /></span>
            <span><span className="block font-serif text-lg font-semibold leading-none text-[#164D59]" data-testid="brand-name">Ameya</span><span className="mt-1 block text-[9px] font-semibold uppercase tracking-[0.22em] text-[#0E776C]" data-testid="brand-tagline">Her Health Connect</span></span>
          </a>
          <nav className="hidden items-center gap-7 lg:flex" aria-label="Main navigation" data-testid="desktop-navigation">
            {["Care pathways", "About Dr. Nisha", "Availability", "Questions"].map((item, index) => <a key={item} href={`#${["care", "about", "availability", "faq"][index]}`} className="text-[13px] font-semibold text-[#35504D] transition-colors duration-300 hover:text-[#0E776C]" data-testid={`nav-${item.toLowerCase().replaceAll(" ", "-")}-link`}>{item}</a>)}
          </nav>
          <Button onClick={scrollToBooking} className="h-10 rounded-sm bg-[#0E776C] px-5 text-sm text-white hover:bg-[#095D54]" data-testid="header-book-button">Book a consultation <ArrowUpRight className="ml-1.5 size-4" /></Button>
        </div>
      </header>

      <main id="top">
        <section className="relative flex min-h-[calc(100svh-2.5rem)] items-end overflow-hidden bg-[#164D59] px-5 pb-20 pt-40 sm:px-8 lg:px-12 lg:pb-24" data-testid="hero-section">
          <img src="https://images.unsplash.com/photo-1758691462651-611d730c5272?auto=format&fit=crop&w=2200&q=85" alt="A warm, attentive healthcare consultation" className="absolute inset-0 h-full w-full object-cover object-center" data-testid="hero-doctor-image" />
          <div className="absolute inset-0 bg-gradient-to-r from-[#123F48]/90 via-[#123F48]/55 to-[#123F48]/10" aria-hidden="true" />
          <div className="absolute inset-x-0 bottom-0 h-32 bg-gradient-to-t from-[#123F48]/55 to-transparent" aria-hidden="true" />
          <div className="relative z-10 mx-auto grid w-full max-w-7xl items-end gap-10 lg:grid-cols-[1fr_0.45fr]">
            <Reveal className="max-w-3xl">
              <div className="mb-7 inline-flex items-center gap-2 rounded-full bg-[#F6D776] px-3.5 py-2 text-xs font-bold uppercase tracking-[0.14em] text-[#164D59]" data-testid="hero-trust-pill"><Sparkles className="size-3.5" /> Care that feels personal</div>
              <h1 className="max-w-3xl font-sans text-5xl font-semibold leading-[0.98] tracking-[-0.045em] text-white sm:text-7xl lg:text-[6.7rem]" data-testid="hero-heading">Her health, <em className="font-serif font-normal text-[#F6D776]">in her hands.</em></h1>
              <p className="mt-7 max-w-xl text-lg leading-relaxed text-white/85 sm:text-xl" data-testid="hero-description">A private, thoughtful place to talk with <strong className="font-semibold text-white">Dr. Nisha Ghelani</strong>, MD (Ob & Gyn), and move forward with clarity.</p>
              <div className="mt-9 flex flex-col gap-3 sm:flex-row">
                <Button onClick={scrollToBooking} className="h-13 rounded-sm bg-[#F6D776] px-6 text-base font-bold text-[#164D59] shadow-[0_14px_30px_rgba(10,35,39,0.25)] hover:-translate-y-0.5 hover:bg-[#FFE49A]" data-testid="hero-book-button">Find your care pathway <ArrowRight className="ml-2 size-4" /></Button>
                <a href="#care" className="inline-flex h-13 items-center justify-center rounded-sm border border-white/60 bg-white/5 px-6 text-base font-semibold text-white backdrop-blur-sm transition-all duration-300 hover:-translate-y-0.5 hover:bg-white hover:text-[#164D59]" data-testid="hero-care-link">Explore care pathways</a>
              </div>
              <div className="mt-10 flex flex-wrap items-center gap-x-6 gap-y-3 text-sm text-white/80" data-testid="hero-contact-strip"><span className="flex items-center gap-2"><ShieldCheck className="size-4 text-[#F6D776]" /> Confidential by design</span><span className="flex items-center gap-2"><Clock3 className="size-4 text-[#F6D776]" /> Tue · Thu · Sat</span></div>
            </Reveal>
            <Reveal className="hidden lg:block" delay={0.12}><div className="border-l border-white/35 pl-7 text-white" data-testid="hero-side-note"><p className="font-mono text-xs uppercase tracking-[0.18em] text-[#F6D776]">Ameya Consultancy</p><p className="mt-4 max-w-[13rem] font-serif text-3xl leading-tight">Twenty-two years of listening.</p><div className="mt-8 flex items-center gap-3 text-xs text-white/75"><span className="flex size-8 items-center justify-center rounded-full bg-white/15"><HeartHandshake className="size-4" /></span> Her Health Connect</div></div></Reveal>
          </div>
        </section>

        <section className="bg-[#003F3A] px-5 py-20 text-white sm:px-8 lg:px-12 lg:py-28" data-testid="trust-strip-section">
          <div className="mx-auto max-w-7xl"><Reveal className="max-w-3xl"><p className="mb-5 text-xs font-bold uppercase tracking-[0.22em] text-[#F6D776]" data-testid="pathway-grid-eyebrow">Care that meets you where you are</p><h2 className="font-sans text-4xl font-medium leading-tight tracking-[-0.035em] sm:text-6xl" data-testid="pathway-grid-heading">Every chapter deserves its own kind of care.</h2><p className="mt-5 max-w-xl text-lg leading-relaxed text-white/70" data-testid="pathway-grid-copy">From first questions to second opinions, the right conversation can change how the next chapter feels.</p></Reveal><div className="mt-12 grid gap-3 sm:grid-cols-2 lg:grid-cols-4"><a href="#care" className="group relative aspect-[0.82] overflow-hidden rounded-sm bg-[#E5B4A9]" data-testid="pathway-card-antenatal"><img src="https://images.unsplash.com/photo-1749065306033-0cb90ff6e283?auto=format&fit=crop&w=900&q=85" alt="Antenatal consultation" className="absolute inset-0 h-full w-full object-cover transition-transform duration-700 group-hover:scale-105" /><div className="absolute inset-0 bg-gradient-to-t from-[#143F3B]/90 via-[#143F3B]/15 to-transparent" /><div className="absolute inset-x-5 bottom-5"><span className="font-mono text-[10px] uppercase tracking-[0.16em] text-[#F6D776]">01</span><h3 className="mt-2 font-serif text-2xl text-white">Antenatal care</h3><p className="mt-1 text-xs text-white/75">Pregnancy, with context.</p></div></a><a href="#care" className="group relative aspect-[0.82] overflow-hidden rounded-sm bg-[#8FD5E1]" data-testid="pathway-card-postnatal"><img src="https://images.unsplash.com/photo-1702788177324-3a4925d4f4cf?auto=format&fit=crop&w=900&q=85" alt="Postnatal mother and baby care" className="absolute inset-0 h-full w-full object-cover transition-transform duration-700 group-hover:scale-105" /><div className="absolute inset-0 bg-gradient-to-t from-[#143F3B]/90 via-[#143F3B]/15 to-transparent" /><div className="absolute inset-x-5 bottom-5"><span className="font-mono text-[10px] uppercase tracking-[0.16em] text-[#F6D776]">02</span><h3 className="mt-2 font-serif text-2xl text-white">Postnatal care</h3><p className="mt-1 text-xs text-white/75">Care for the person, too.</p></div></a><a href="#care" className="group relative aspect-[0.82] overflow-hidden rounded-sm bg-[#E9D277]" data-testid="pathway-card-puberty"><img src="https://images.unsplash.com/photo-1638202993928-7267aad84c31?auto=format&fit=crop&w=900&q=85" alt="Warm women's health clinic" className="absolute inset-0 h-full w-full object-cover transition-transform duration-700 group-hover:scale-105" /><div className="absolute inset-0 bg-gradient-to-t from-[#143F3B]/90 via-[#143F3B]/15 to-transparent" /><div className="absolute inset-x-5 bottom-5"><span className="font-mono text-[10px] uppercase tracking-[0.16em] text-[#F6D776]">03</span><h3 className="mt-2 font-serif text-2xl text-white">Puberty & cycles</h3><p className="mt-1 text-xs text-white/75">Private questions welcome.</p></div></a><a href="#care" className="group relative aspect-[0.82] overflow-hidden rounded-sm bg-[#B7D5C7]" data-testid="pathway-card-menopause"><img src="https://images.pexels.com/photos/6749765/pexels-photo-6749765.jpeg?auto=compress&cs=tinysrgb&w=900" alt="Doctor ready to listen" className="absolute inset-0 h-full w-full object-cover transition-transform duration-700 group-hover:scale-105" /><div className="absolute inset-0 bg-gradient-to-t from-[#143F3B]/90 via-[#143F3B]/15 to-transparent" /><div className="absolute inset-x-5 bottom-5"><span className="font-mono text-[10px] uppercase tracking-[0.16em] text-[#F6D776]">04</span><h3 className="mt-2 font-serif text-2xl text-white">Menopause & more</h3><p className="mt-1 text-xs text-white/75">A new rhythm, supported.</p></div></a></div></div>
        </section>

        <section id="about" className="bg-[#F4F1E8] px-5 py-24 sm:px-8 lg:px-12 lg:py-32" data-testid="about-section">
          <div className="mx-auto max-w-7xl"><div className="grid gap-14 lg:grid-cols-[0.8fr_1.2fr] lg:gap-24"><Reveal><p className="mb-5 text-xs font-bold uppercase tracking-[0.22em] text-[#0E776C]" data-testid="about-eyebrow">Meet your doctor</p><h2 className="max-w-sm font-sans text-4xl font-medium leading-tight tracking-[-0.035em] text-[#164D59] sm:text-6xl" data-testid="about-heading">Medicine begins with feeling heard.</h2></Reveal><Reveal className="max-w-2xl" delay={0.1}><p className="text-xl leading-relaxed text-[#35504D]" data-testid="about-intro">Dr. Nisha Ghelani believes a consultation should leave you with more than a prescription. It should leave you with clarity, a plan, and the confidence to ask the next question.</p><div className="mt-10 grid gap-8 border-t border-[#C9D3C6] pt-8 sm:grid-cols-3"><div data-testid="about-stat-experience"><span className="font-serif text-5xl text-[#0E776C]">22</span><span className="mt-2 block text-xs font-bold uppercase tracking-[0.14em] text-[#35504D]">Years of experience</span></div><div data-testid="about-stat-approach"><span className="font-serif text-5xl text-[#0E776C]">1:1</span><span className="mt-2 block text-xs font-bold uppercase tracking-[0.14em] text-[#35504D]">Personal attention</span></div><div data-testid="about-stat-care"><span className="font-serif text-5xl text-[#0E776C]">100%</span><span className="mt-2 block text-xs font-bold uppercase tracking-[0.14em] text-[#35504D]">Confidential care</span></div></div></Reveal></div>
          <Reveal className="mx-auto mt-16 grid max-w-7xl items-end gap-8 rounded-sm bg-[#0E776C] p-7 text-white sm:p-10 lg:grid-cols-[1fr_0.65fr] lg:p-14" delay={0.08}><div><p className="text-xs font-bold uppercase tracking-[0.2em] text-[#F6D776]" data-testid="philosophy-label">Her care philosophy</p><blockquote className="mt-5 max-w-2xl font-serif text-3xl leading-tight sm:text-4xl" data-testid="philosophy-quote">“There is no small question when it comes to your health. We make time for all of them.”</blockquote></div><div className="border-t border-white/20 pt-6 lg:border-l lg:border-t-0 lg:pl-8 lg:pt-0"><p className="text-sm leading-relaxed text-white/75" data-testid="philosophy-copy">Whether you are preparing for motherhood, finding your footing after birth, navigating a new stage, or simply seeking another perspective—this is a place to pause and talk it through.</p></div></Reveal></div>
        </section>

        <section id="care" className="bg-[#8FD5E1]" data-testid="care-section"><div className="mx-auto max-w-7xl px-5 py-24 sm:px-8 lg:px-12 lg:py-32"><Reveal className="max-w-2xl"><p className="mb-5 text-xs font-bold uppercase tracking-[0.22em] text-[#0E776C]" data-testid="care-eyebrow">Care pathways</p><h2 className="font-sans text-4xl font-medium leading-tight tracking-[-0.035em] text-[#164D59] sm:text-6xl" data-testid="care-heading">The right conversation for where you are.</h2><p className="mt-5 text-lg leading-relaxed text-[#35504D]" data-testid="care-intro">Choose a pathway to see how Dr. Nisha can support you—with expertise, context, and no rush.</p></Reveal><div className="mt-12 grid gap-10 lg:grid-cols-[0.42fr_0.58fr] lg:gap-20"><div className="flex flex-col gap-2" role="tablist" aria-label="Care pathways" data-testid="care-pathway-tabs">{focusAreas.map((area, index) => <button key={area.id} role="tab" aria-selected={activeFocus === area.id} onClick={() => setActiveFocus(area.id)} className={`group flex items-center justify-between border-b px-1 py-4 text-left transition-colors duration-300 ${activeFocus === area.id ? "border-[#164D59] text-[#164D59]" : "border-[#5FB5B7]/60 text-[#35504D] hover:text-[#164D59]"}`} data-testid={`care-tab-${area.id}`}><span className="flex items-center gap-4"><span className={`font-mono text-xs ${activeFocus === area.id ? "text-[#0E776C]" : "text-[#35504D]"}`}>0{index + 1}</span><span className="font-serif text-xl">{area.title}</span></span><ArrowUpRight className={`size-4 transition-transform duration-300 ${activeFocus === area.id ? "translate-x-1 -translate-y-1 text-[#0E776C]" : "opacity-0 group-hover:opacity-100"}`} /></button>)}</div><motion.div key={activeArea.id} initial={{ opacity: 0, x: 12 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.4 }} className="rounded-sm border border-white/70 bg-white p-7 shadow-[0_18px_50px_rgba(22,77,89,0.12)] sm:p-10" role="tabpanel" data-testid="care-pathway-panel"><div className="flex items-center justify-between"><Badge className="border-[#C8E3DB] bg-[#EAF2F1] text-[#0E776C]" data-testid="care-pathway-eyebrow">{activeArea.eyebrow}</Badge><span className="font-mono text-xs text-[#35504D]" data-testid="care-pathway-id">{activeArea.id}</span></div><h3 className="mt-8 max-w-lg font-serif text-3xl leading-tight text-[#164D59] sm:text-4xl" data-testid="care-pathway-heading">{activeArea.heading}</h3><p className="mt-5 max-w-xl text-base leading-relaxed text-[#35504D]" data-testid="care-pathway-description">{activeArea.body}</p><ul className="mt-8 grid gap-3 sm:grid-cols-2" data-testid="care-pathway-points">{activeArea.points.map((point) => <li key={point} className="flex items-center gap-2 text-sm text-[#263D3A]"><Check className="size-4 text-[#E07A5F]" /> {point}</li>)}</ul><Button onClick={scrollToBooking} className="mt-10 rounded-sm bg-[#0E776C] text-white hover:bg-[#095D54]" data-testid="care-pathway-book-button">Book this pathway <ArrowRight className="ml-2 size-4" /></Button></motion.div></div></div></section>

        <section id="booking" className="scroll-mt-20 mx-auto max-w-7xl px-5 py-24 sm:px-8 lg:px-12 lg:py-32" data-testid="booking-section"><div className="grid gap-12 lg:grid-cols-[0.72fr_1.28fr] lg:gap-20"><Reveal className="lg:sticky lg:top-28 lg:self-start"><p className="mb-5 text-xs font-bold uppercase tracking-[0.22em] text-[#E07A5F]" data-testid="booking-eyebrow">Start with a conversation</p><h2 className="font-serif text-4xl leading-tight text-[#114B5F] sm:text-5xl" data-testid="booking-heading">Tell us what would feel helpful.</h2><p className="mt-5 max-w-md text-lg leading-relaxed text-[#5C6479]" data-testid="booking-intro">Share a little about what you are looking for. This is a request, not a commitment—we will confirm the details with you personally.</p><div className="mt-8 space-y-4 text-sm text-[#5C6479]"><a href="tel:+916355734167" className="flex items-center gap-3 font-semibold text-[#114B5F] hover:text-[#E07A5F]" data-testid="booking-phone-link"><Phone className="size-4" /> +91 63557 34167</a><a href="mailto:nishaghelani78@gmail.com" className="flex items-center gap-3 font-semibold text-[#114B5F] hover:text-[#E07A5F]" data-testid="booking-email-link"><Mail className="size-4" /> nishaghelani78@gmail.com</a></div></Reveal><Reveal className="rounded-[1.5rem] border border-[#E5DEC9] bg-white p-6 shadow-[0_20px_60px_rgba(17,75,95,0.08)] sm:p-10" delay={0.1}><div className="mb-8 flex items-start justify-between gap-4 border-b border-[#E5DEC9] pb-6"><div><h3 className="font-serif text-2xl text-[#114B5F]" data-testid="booking-form-heading">Request your consultation</h3><p className="mt-1 text-sm text-[#5C6479]" data-testid="booking-form-subheading">We typically reply within one working day.</p></div><CalendarDays className="size-6 text-[#E07A5F]" /></div><BookingForm onCreated={handleCreated} testIdPrefix="appointment" /></Reveal></div></section>

        <section id="availability" className="border-y border-[#E5DEC9] bg-[#F4F0EA]" data-testid="availability-section"><div className="mx-auto max-w-7xl px-5 py-24 sm:px-8 lg:px-12 lg:py-28"><div className="grid gap-12 lg:grid-cols-[0.6fr_1.4fr] lg:items-end"><Reveal><p className="mb-5 text-xs font-bold uppercase tracking-[0.22em] text-[#E07A5F]" data-testid="availability-eyebrow">Consultation logistics</p><h2 className="font-serif text-4xl leading-tight text-[#114B5F] sm:text-5xl" data-testid="availability-heading">A weekly rhythm, made for thoughtful care.</h2><p className="mt-5 max-w-md text-lg leading-relaxed text-[#5C6479]" data-testid="availability-copy">Appointments are available on three days each week, by request. We will confirm the exact time with you after receiving your details.</p></Reveal><Reveal className="grid grid-cols-2 gap-2 sm:grid-cols-4 lg:grid-cols-7" delay={0.1}>{weeklyCadence.map((item) => { const open = item.status !== "Closed"; return <div key={item.day} className={`min-h-32 rounded-xl border p-3 transition-transform duration-300 hover:-translate-y-1 ${open ? "border-[#A9C8C0] bg-[#EAF2F1]" : "border-[#E5DEC9] bg-[#FAF8F5]"}`} data-testid={`availability-${item.short.toLowerCase()}`}><span className="font-mono text-[10px] font-bold tracking-[0.14em] text-[#839788]">{item.short}</span><span className="mt-7 block font-serif text-base text-[#114B5F]">{item.day}</span><span className={`mt-2 inline-flex rounded-full px-2 py-1 text-[10px] font-semibold ${open ? "bg-[#D6E1DC] text-[#1A5E72]" : "bg-[#EDE9E2] text-[#5C6479]"}`}>{open ? "Available" : "Closed"}</span><span className="mt-2 block text-[10px] leading-tight text-[#5C6479]">{item.note}</span></div>; })}</Reveal></div><div className="mt-10 flex flex-wrap items-center gap-x-8 gap-y-3 border-t border-[#E5DEC9] pt-6 text-sm text-[#5C6479]" data-testid="availability-notes"><span className="flex items-center gap-2"><Clock3 className="size-4 text-[#E07A5F]" /> Time confirmed personally</span><span className="flex items-center gap-2"><MapPin className="size-4 text-[#E07A5F]" /> Clinic or video, as preferred</span></div></div></section>

        <section id="faq" className="mx-auto max-w-7xl px-5 py-24 sm:px-8 lg:px-12 lg:py-32" data-testid="faq-section"><div className="grid gap-12 lg:grid-cols-[0.7fr_1.3fr] lg:gap-24"><Reveal><p className="mb-5 text-xs font-bold uppercase tracking-[0.22em] text-[#E07A5F]" data-testid="faq-eyebrow">A few answers</p><h2 className="font-serif text-4xl leading-tight text-[#114B5F] sm:text-5xl" data-testid="faq-heading">Before we meet.</h2><p className="mt-5 max-w-sm text-lg leading-relaxed text-[#5C6479]" data-testid="faq-intro">Good care starts with clarity. Here are a few things patients often want to know.</p></Reveal><Reveal className="divide-y divide-[#E5DEC9] border-y border-[#E5DEC9]" delay={0.1}>{faqs.map((faq, index) => <div key={faq.question} data-testid={`faq-item-${index + 1}`}><button type="button" aria-expanded={openFaq === index} onClick={() => setOpenFaq(openFaq === index ? -1 : index)} className="flex min-h-16 w-full items-center justify-between gap-5 py-5 text-left font-serif text-xl text-[#114B5F]" data-testid={`faq-question-${index + 1}`}>{faq.question}<ChevronDown className={`size-5 shrink-0 text-[#E07A5F] transition-transform duration-300 ${openFaq === index ? "rotate-180" : ""}`} /></button>{openFaq === index && <p className="max-w-2xl pb-6 pr-8 text-sm leading-relaxed text-[#5C6479]" data-testid={`faq-answer-${index + 1}`}>{faq.answer}</p>}</div>)}</Reveal></div></section>
      </main>

      <footer className="bg-[#114B5F] text-white" data-testid="site-footer"><div className="mx-auto max-w-7xl px-5 py-12 sm:px-8 lg:px-12"><div className="grid gap-10 border-b border-white/15 pb-10 lg:grid-cols-[1.2fr_0.8fr_0.8fr]"><div><div className="flex items-center gap-3"><span className="flex size-10 items-center justify-center rounded-full bg-[#E07A5F] text-white"><HeartHandshake className="size-5" /></span><span className="font-serif text-xl" data-testid="footer-brand">Ameya Consultancy</span></div><p className="mt-5 max-w-sm text-sm leading-relaxed text-white/65" data-testid="footer-description">Her Health Connect—a private space for expert women's health conversations with Dr. Nisha Ghelani.</p></div><div><p className="text-xs font-bold uppercase tracking-[0.18em] text-[#F4C2B4]" data-testid="footer-contact-label">Contact</p><div className="mt-4 space-y-3 text-sm text-white/75"><a href="tel:+916355734167" className="flex items-center gap-2 hover:text-white" data-testid="footer-phone-link"><Phone className="size-4" /> +91 63557 34167</a><a href="mailto:nishaghelani78@gmail.com" className="flex items-center gap-2 break-all hover:text-white" data-testid="footer-email-link"><Mail className="size-4" /> nishaghelani78@gmail.com</a></div></div><div><p className="text-xs font-bold uppercase tracking-[0.18em] text-[#F4C2B4]" data-testid="footer-availability-label">Availability</p><p className="mt-4 text-sm leading-relaxed text-white/75" data-testid="footer-availability-copy">Tuesday, Thursday & Saturday<br />By appointment only</p><Button onClick={scrollToBooking} variant="outline" className="mt-5 rounded-full border-white/30 bg-transparent text-white hover:bg-white hover:text-[#114B5F]" data-testid="footer-book-button">Request a time <ArrowUpRight className="ml-1.5 size-4" /></Button></div></div><div className="mt-8 rounded-2xl border border-[#F4C2B4]/35 bg-[#0d3b4b] p-5" data-testid="statutory-notice"><p className="text-xs font-bold uppercase tracking-[0.18em] text-[#F4C2B4]">Important care notice</p><p className="mt-2 max-w-3xl text-sm leading-relaxed text-white/75">Ameya Consultancy is for planned consultations and expert advice. It is not an emergency service. For acute pain, heavy bleeding, breathing difficulty, or any obstetric emergency, please contact your nearest hospital emergency department immediately.</p></div><p className="mt-8 text-xs text-white/45" data-testid="footer-copyright">© {new Date().getFullYear()} Ameya Consultancy · Dr. Nisha Ghelani, MD (Ob & Gyn)</p></div></footer>

      <div className="fixed inset-x-0 bottom-0 z-50 grid grid-cols-2 gap-2 border-t border-[#E5DEC9] bg-[#FAF8F5]/95 p-3 shadow-[0_-10px_30px_rgba(17,75,95,0.12)] backdrop-blur-md md:hidden" data-testid="mobile-quick-action-bar"><a href="tel:+916355734167" className="flex min-h-12 items-center justify-center gap-2 rounded-full border border-[#114B5F] bg-transparent text-sm font-semibold text-[#114B5F]" data-testid="mobile-call-doctor-button"><Phone className="size-4" /> Call doctor</a><Button onClick={() => setMobileBookingOpen(true)} className="min-h-12 rounded-full bg-[#E07A5F] text-sm text-white hover:bg-[#c9654c]" data-testid="mobile-book-button"><CalendarDays className="mr-2 size-4" /> Book consultation</Button></div>

      <Dialog open={mobileBookingOpen} onOpenChange={setMobileBookingOpen}><DialogContent className="left-0 top-auto bottom-0 max-h-[92vh] w-full max-w-none translate-x-0 translate-y-0 overflow-y-auto rounded-b-none rounded-t-[2rem] border-[#E5DEC9] bg-[#FAF8F5] p-5 sm:p-8 md:left-[50%] md:top-[50%] md:bottom-auto md:max-w-lg md:translate-x-[-50%] md:translate-y-[-50%] md:rounded-2xl" data-testid="mobile-booking-sheet"><DialogHeader><DialogTitle className="font-serif text-2xl text-[#114B5F]" data-testid="mobile-booking-title">Request a consultation</DialogTitle><DialogDescription data-testid="mobile-booking-description">A private request, confirmed personally.</DialogDescription></DialogHeader><div className="mt-4"><BookingForm onCreated={handleCreated} testIdPrefix="mobile-appointment" /></div></DialogContent></Dialog>
      <Dialog open={confirmationOpen} onOpenChange={setConfirmationOpen}><DialogContent className="max-w-md border-[#E5DEC9] bg-[#FAF8F5]" data-testid="appointment-confirmation-dialog"><DialogHeader><div className="mb-3 flex size-12 items-center justify-center rounded-full bg-[#D6E1DC] text-[#1A5E72]"><Check className="size-6" /></div><DialogTitle className="font-serif text-3xl text-[#114B5F]" data-testid="confirmation-title">Your request is with us.</DialogTitle><DialogDescription className="text-base leading-relaxed" data-testid="confirmation-description">Thank you, {confirmedAppointment?.full_name}. Dr. Nisha's team will contact you to confirm the time.</DialogDescription></DialogHeader><div className="mt-5 rounded-xl border border-[#E5DEC9] bg-white p-4" data-testid="confirmation-reference-card"><p className="text-xs font-bold uppercase tracking-[0.16em] text-[#839788]">Request reference</p><p className="mt-1 font-mono text-xl font-semibold text-[#114B5F]" data-testid="confirmation-reference">{confirmedAppointment?.reference}</p><p className="mt-3 text-sm text-[#5C6479]" data-testid="confirmation-contact-copy">Need help sooner? Call <a href="tel:+916355734167" className="font-semibold text-[#114B5F] underline" data-testid="confirmation-phone-link">+91 63557 34167</a>.</p></div><p className="mt-5 text-sm leading-relaxed text-[#5C6479]" data-testid="confirmation-privacy-copy">Please keep your reference handy. Your details remain private and are used only to coordinate this consultation.</p></DialogContent></Dialog>
    </div>
  );
}