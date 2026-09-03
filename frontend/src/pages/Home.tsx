import { useState, type ChangeEvent, type FormEvent, type ReactNode } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { motion, useReducedMotion } from "motion/react";
import {
  ArrowRight,
  ArrowUpRight,
  CalendarDays,
  Check,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Clock3,
  FileText,
  HeartHandshake,
  Mail,
  MessageCircle,
  Paperclip,
  Phone,
  ShieldCheck,
  Trash2,
  Video,
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
import { ApiError, apiGet, apiPost, apiUpload } from "@/lib/api";

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
  attachment_ids: string[];
}

interface Appointment extends AppointmentCreate {
  id: string;
  reference: string;
  status: "requested";
  meeting_status: "pending_connection" | "scheduled";
  meeting_url: string | null;
  created_at: string;
}

interface AvailableDate {
  date: string;
  day_label: string;
  display_label: string;
}

interface BookingOptions {
  timezone: string;
  available_days: string[];
  available_dates: AvailableDate[];
  available_times: string[];
  google_meet_enabled: boolean;
}

interface AppointmentAttachment {
  id: string;
  file_name: string;
  content_type: string;
  size: number;
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
    body: "A careful review of ultrasound scans, lab reports, surgical proposals, and complex gynaecology diagnoses, grounded in more than 20 years of insight.",
    points: ["Reports and checkup review", "Surgical proposal discussion", "Complex diagnosis perspective"],
  },
];

const faqs = [
  {
    question: "What happens after I book?",
    answer: "Your appointment preference is saved securely and a reference number is shown immediately. Dr. Nisha's team will reach out on the phone or email you provided to confirm the details.",
  },
  {
    question: "How will my Google Meet consultation work?",
    answer: "Choose an available date and exact time in the booking calendar. Once Google Calendar is connected, the Meet link will be created immediately and sent to your email.",
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
  consultation_type: "video_consultation",
  focus_area: "antenatal",
  preferred_date: "",
  preferred_time: "10:00 AM",
  notes: "",
  attachment_ids: [],
};

const AMEYA_LOGO_URL = "https://customer-assets-7cd3h4nn.emergentagent.net/job_ameya-health/artifacts/feu0o2dt_WhatsApp%20Image%202026-09-02%20at%2023.19.22.jpeg";
const DR_NISHA_PORTRAIT_URL = "https://static.prod-images.emergentagent.com/jobs/4300b7d0-3e0e-4e6d-9e63-96dcd8e088e8/images/30aeb9a1dedcb0a3875e95b0e8bbe0789a325f5faf654bb805b9f25a91b9b8ca.jpeg";
const DR_NISHA_DELIVERY_URL = "https://static.prod-images.emergentagent.com/jobs/4300b7d0-3e0e-4e6d-9e63-96dcd8e088e8/images/d49ce7c1b82c93ff15773c7454cf1b08bb44a8b1d95614401abbd9d89a5193f6.jpeg";
const fetchBookingOptions = () => apiGet<BookingOptions>("/appointments/options");
const HERO_VIDEO_URL = "https://videos.pexels.com/video-files/7579333/7579333-sd_506_960_25fps.mp4";
const WHATSAPP_URL = "https://wa.me/916355734167?text=Hello%20Dr.%20Nisha%2C%20I%20would%20like%20to%20book%20a%20consultation.";
const careStories = [
  { id: "antenatal", number: "01", title: "Antenatal care", note: "Pregnancy guidance with time for every question.", image: "https://images.unsplash.com/photo-1749065306033-0cb90ff6e283?auto=format&fit=crop&w=1000&q=88" },
  { id: "postnatal", number: "02", title: "Postnatal recovery", note: "Care for the mother, not only the milestone.", image: DR_NISHA_DELIVERY_URL },
  { id: "puberty", number: "03", title: "Puberty & cycles", note: "A private place for first questions.", image: "https://images.unsplash.com/photo-1638202993928-7267aad84c31?auto=format&fit=crop&w=1000&q=88" },
  { id: "menopause", number: "04", title: "Menopause care", note: "Practical support for a new rhythm.", image: DR_NISHA_PORTRAIT_URL },
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
  const [calendarIndex, setCalendarIndex] = useState(0);
  const [files, setFiles] = useState<File[]>([]);
  const bookingOptions = useQuery({
    queryKey: ["booking-options"],
    queryFn: fetchBookingOptions,
    retry: false,
    staleTime: 15 * 60 * 1000,
  });
  const mutation = useMutation({
    mutationFn: async (payload: AppointmentCreate) => {
      const attachments: AppointmentAttachment[] = [];
      for (const file of files) {
        const body = new FormData();
        body.append("file", file);
        attachments.push(await apiUpload<AppointmentAttachment>("/appointments/attachments", body));
      }
      return apiPost<Appointment>("/appointments", {
        ...payload,
        attachment_ids: attachments.map((attachment) => attachment.id),
      });
    },
    onSuccess: (appointment) => {
      toast.success("Appointment preference saved", { description: `Reference ${appointment.reference}` });
      setForm(initialForm);
      setDateError("");
      setFiles([]);
      setCalendarIndex(0);
      onCreated(appointment);
    },
  });

  const updateField = (field: keyof AppointmentCreate) => (event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    setForm((current) => ({ ...current, [field]: event.target.value }));
    if (field === "preferred_date") setDateError("");
  };

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!form.preferred_date) {
      setDateError("Please choose a preferred consultation date.");
      return;
    }
    const selectedDate = new Date(`${form.preferred_date}T12:00:00`);
    if (Number.isNaN(selectedDate.getTime()) || [0, 1, 3, 5].includes(selectedDate.getDay())) {
      setDateError("Please choose Tuesday, Thursday, or Saturday.");
      return;
    }
    setDateError("");
    mutation.mutate(form);
  };

  const handleFiles = (event: ChangeEvent<HTMLInputElement>) => {
    const selected = Array.from(event.target.files ?? []);
    event.target.value = "";
    if (files.length + selected.length > 3) {
      toast.error("You can attach up to three reports.");
      return;
    }
    const allowedTypes = new Set(["application/pdf", "image/jpeg", "image/png"]);
    const invalid = selected.find((file) => !allowedTypes.has(file.type) || file.size > 10 * 1024 * 1024);
    if (invalid) {
      toast.error("Use PDF, JPG, or PNG files up to 10 MB each.");
      return;
    }
    setFiles((current) => [...current, ...selected]);
  };

  const availableDates = bookingOptions.data?.available_dates ?? [];
  const monthKeys = Array.from(new Set(availableDates.map((option) => option.date.slice(0, 7))));
  const monthKey = monthKeys[calendarIndex] ?? monthKeys[0] ?? "";
  const monthStart = monthKey ? new Date(`${monthKey}-01T12:00:00`) : null;
  const monthLabel = monthStart?.toLocaleDateString("en-IN", { month: "long", year: "numeric" }) ?? "Loading calendar";
  const daysInMonth = monthStart ? new Date(monthStart.getFullYear(), monthStart.getMonth() + 1, 0).getDate() : 0;
  const firstWeekday = monthStart?.getDay() ?? 0;
  const availableDateSet = new Set(availableDates.map((option) => option.date));

  const errorMessage = mutation.error instanceof ApiError && mutation.error.status === 422
    ? "Please check the selected date, time, files, and contact details."
    : mutation.error
      ? "We couldn't save the appointment. Please call or WhatsApp Dr. Nisha directly."
      : "";

  return (
    <form onSubmit={handleSubmit} className="space-y-8" data-testid={testId("booking-form")}>
      <div className={`flex items-start gap-3 rounded-2xl border p-4 ${bookingOptions.data?.google_meet_enabled ? "border-[#B8DAD2] bg-[#EAF2F1]" : "border-[#E7D59B] bg-[#FFF8DC]"}`} data-testid={testId("meet-status")}><Video className="mt-0.5 size-5 shrink-0 text-[#0E776C]" /><div><p className="text-sm font-bold text-[#164D59]">Google Meet consultation</p><p className="mt-1 text-xs leading-relaxed text-[#52706B]">{bookingOptions.data?.google_meet_enabled ? "Your Meet link will be created immediately and emailed after booking." : "Calendar connection is not active yet. Your time can be saved, but a Meet link cannot be created until Dr. Nisha connects Google Calendar."}</p></div></div>

      <div className="grid gap-8 lg:grid-cols-[0.9fr_1.1fr]">
        <section className="space-y-5" data-testid={testId("care-section")}><div><p className="text-[10px] font-bold uppercase tracking-[0.18em] text-[#E07A5F]">Step 1</p><h4 className="mt-2 font-serif text-2xl text-[#164D59]" data-testid={testId("care-heading")}>What would you like to discuss?</h4></div><div className="space-y-2"><Label htmlFor={`${testIdPrefix}-focus-area`}>Care pathway</Label><select id={`${testIdPrefix}-focus-area`} required value={form.focus_area} onChange={updateField("focus_area")} className="flex h-12 w-full rounded-xl border border-[#D9DFD4] bg-white px-3 text-sm text-[#2B2D42] outline-none ring-offset-white transition focus:border-[#0E776C] focus:ring-2 focus:ring-[#0E776C]/20" data-testid={testId("focus-select")}>{focusAreas.map((area) => <option key={area.id} value={area.id}>{area.title}</option>)}</select></div><div className="rounded-2xl bg-[#F4F1E8] p-4"><p className="text-xs font-bold uppercase tracking-[0.14em] text-[#0E776C]">Video consultation</p><p className="mt-2 text-sm leading-relaxed text-[#52706B]">Private 1:1 consultation on Google Meet. Please join from a quiet place with your reports nearby.</p></div></section>

        <section className="space-y-4" data-testid={testId("schedule-section")}><div className="flex items-end justify-between gap-3"><div><p className="text-[10px] font-bold uppercase tracking-[0.18em] text-[#E07A5F]">Step 2</p><h4 className="mt-2 font-serif text-2xl text-[#164D59]" data-testid={testId("schedule-heading")}>Choose a date</h4></div><span className="text-[10px] font-bold uppercase tracking-[0.12em] text-[#839788]">Tue · Thu · Sat</span></div><div className="rounded-2xl border border-[#D9DFD4] bg-[#FFFDF8] p-4" data-testid={testId("calendar")}><div className="mb-4 flex items-center justify-between"><button type="button" disabled={calendarIndex === 0} onClick={() => setCalendarIndex((value) => Math.max(0, value - 1))} className="flex size-9 items-center justify-center rounded-full border border-[#D9DFD4] text-[#164D59] disabled:opacity-30" aria-label="Previous month" data-testid={testId("calendar-previous")}><ChevronLeft className="size-4" /></button><p className="font-serif text-lg text-[#164D59]" data-testid={testId("calendar-month")}>{monthLabel}</p><button type="button" disabled={calendarIndex >= monthKeys.length - 1} onClick={() => setCalendarIndex((value) => Math.min(monthKeys.length - 1, value + 1))} className="flex size-9 items-center justify-center rounded-full border border-[#D9DFD4] text-[#164D59] disabled:opacity-30" aria-label="Next month" data-testid={testId("calendar-next")}><ChevronRight className="size-4" /></button></div><div className="grid grid-cols-7 gap-1 text-center">{["S", "M", "T", "W", "T", "F", "S"].map((day, index) => <span key={`${day}-${index}`} className="py-1 text-[10px] font-bold text-[#839788]">{day}</span>)}{Array.from({ length: firstWeekday }).map((_, index) => <span key={`blank-${index}`} />)}{Array.from({ length: daysInMonth }).map((_, index) => { const day = index + 1; const dateValue = `${monthKey}-${String(day).padStart(2, "0")}`; const available = availableDateSet.has(dateValue); const selected = form.preferred_date === dateValue; return <button key={dateValue} type="button" disabled={!available} onClick={() => { setForm((current) => ({ ...current, preferred_date: dateValue })); setDateError(""); }} className={`aspect-square rounded-lg text-xs font-semibold transition-colors duration-200 ${selected ? "bg-[#0E776C] text-white" : available ? "bg-[#EAF2F1] text-[#0E776C] hover:bg-[#CFE3DD]" : "text-[#C6CBC6]"}`} data-testid={testId(`calendar-day-${dateValue}`)}>{day}</button>; })}</div></div>{dateError && <p className="text-sm font-medium text-[#B84F3A]" role="alert" data-testid={testId("date-error")}>{dateError}</p>}</section>
      </div>

      <fieldset className="space-y-3 border-t border-[#E5DEC9] pt-7" data-testid={testId("time-section")}><div className="flex items-center justify-between"><legend className="font-serif text-xl text-[#164D59]">Choose a time</legend><span className="text-xs text-[#839788]">India time · 10 AM–6 PM</span></div><div className="grid grid-cols-3 gap-2 sm:grid-cols-5">{(bookingOptions.data?.available_times ?? ["10:00 AM", "11:00 AM", "12:00 PM", "1:00 PM", "2:00 PM", "3:00 PM", "4:00 PM", "5:00 PM", "6:00 PM"]).map((time) => <button key={time} type="button" aria-pressed={form.preferred_time === time} onClick={() => setForm((current) => ({ ...current, preferred_time: time }))} className={`min-h-11 rounded-xl border px-2 text-sm transition-all duration-200 ${form.preferred_time === time ? "border-[#0E776C] bg-[#0E776C] text-white" : "border-[#D9DFD4] bg-white text-[#52706B] hover:border-[#0E776C]"}`} data-testid={testId(`time-${time.replace(/[: ]/g, "-").toLowerCase()}`)}>{time}</button>)}</div></fieldset>

      <section className="space-y-5 border-t border-[#E5DEC9] pt-7" data-testid={testId("details-section")}><div><p className="text-[10px] font-bold uppercase tracking-[0.18em] text-[#E07A5F]">Step 3</p><h4 className="mt-2 font-serif text-2xl text-[#164D59]" data-testid={testId("details-heading")}>Your details</h4></div><div className="grid gap-5 sm:grid-cols-2"><div className="space-y-2"><Label htmlFor={`${testIdPrefix}-full-name`}>Your name</Label><Input id={`${testIdPrefix}-full-name`} required value={form.full_name} onChange={updateField("full_name")} placeholder="Full name" data-testid={testId("name-input")} /></div><div className="space-y-2"><Label htmlFor={`${testIdPrefix}-phone`}>Phone number</Label><Input id={`${testIdPrefix}-phone`} required value={form.phone} onChange={updateField("phone")} placeholder="+91 ..." data-testid={testId("phone-input")} /></div></div><div className="space-y-2"><Label htmlFor={`${testIdPrefix}-email`}>Email address</Label><Input id={`${testIdPrefix}-email`} type="email" required value={form.email} onChange={updateField("email")} placeholder="you@example.com" data-testid={testId("email-input")} /></div><div className="space-y-2"><Label htmlFor={`${testIdPrefix}-notes`}>What would you like to discuss? <span className="font-normal text-[#5C6479]">(optional)</span></Label><Textarea id={`${testIdPrefix}-notes`} value={form.notes} onChange={updateField("notes")} placeholder="A few words are enough..." className="min-h-20 resize-none" data-testid={testId("notes-input")} /></div>

        <div className="space-y-3"><div className="flex items-center justify-between"><Label htmlFor={`${testIdPrefix}-attachments`}>Attach reports <span className="font-normal text-[#839788]">(optional)</span></Label><span className="text-[10px] uppercase tracking-[0.1em] text-[#839788]">PDF, JPG, PNG · 10 MB</span></div><input id={`${testIdPrefix}-attachments`} type="file" accept=".pdf,.jpg,.jpeg,.png,application/pdf,image/jpeg,image/png" multiple onChange={handleFiles} className="sr-only" data-testid={testId("file-input")} /><label htmlFor={`${testIdPrefix}-attachments`} className="flex min-h-20 cursor-pointer items-center justify-center gap-3 rounded-2xl border border-dashed border-[#A9BEB5] bg-[#FAFCFA] px-4 text-sm font-semibold text-[#0E776C] transition-colors duration-200 hover:border-[#0E776C] hover:bg-[#EAF2F1]" data-testid={testId("file-picker")}><Paperclip className="size-5" /> Add reports or images</label>{files.length > 0 && <div className="space-y-2" data-testid={testId("file-list")}>{files.map((file, index) => <div key={`${file.name}-${file.size}`} className="flex items-center justify-between rounded-xl bg-[#F4F1E8] px-3 py-2 text-sm"><span className="flex min-w-0 items-center gap-2"><FileText className="size-4 shrink-0 text-[#0E776C]" /><span className="truncate">{file.name}</span></span><button type="button" onClick={() => setFiles((current) => current.filter((_, fileIndex) => fileIndex !== index))} className="ml-3 flex size-8 shrink-0 items-center justify-center rounded-full text-[#B84F3A] hover:bg-white" aria-label={`Remove ${file.name}`} data-testid={testId(`file-remove-${index}`)}><Trash2 className="size-4" /></button></div>)}</div>}</div></section>

      {errorMessage && <p className="text-sm font-medium text-[#B84F3A]" role="alert" data-testid={testId("form-error")}>{errorMessage}</p>}
      <Button type="submit" disabled={mutation.isPending} className="h-13 w-full rounded-full bg-[#E07A5F] text-white shadow-[0_10px_24px_rgba(224,122,95,0.22)] hover:bg-[#c9654c]" data-testid={testId("submit-button")}>{mutation.isPending ? "Saving appointment..." : "Book my appointment"}{!mutation.isPending && <ArrowRight className="ml-2 size-4" />}</Button>
      <p className="flex items-start gap-2 text-xs leading-relaxed text-[#5C6479]" data-testid={testId("privacy-note")}><ShieldCheck className="mt-0.5 size-4 shrink-0 text-[#1A5E72]" /> Reports are stored privately with this appointment. No payment is taken now.</p>
    </form>
  );
}

export default function Home() {
  const reduceMotion = useReducedMotion();
  const [activeFocus, setActiveFocus] = useState(focusAreas[0].id);
  const [openFaq, setOpenFaq] = useState(0);
  const [bookingOpen, setBookingOpen] = useState(false);
  const [confirmationOpen, setConfirmationOpen] = useState(false);
  const [confirmedAppointment, setConfirmedAppointment] = useState<Appointment | null>(null);
  const activeArea = focusAreas.find((area) => area.id === activeFocus) ?? focusAreas[0];

  const openBooking = () => setBookingOpen(true);
  const scrollToBooking = openBooking;
  const handleCreated = (appointment: Appointment) => {
    setConfirmedAppointment(appointment);
    setBookingOpen(false);
    setConfirmationOpen(true);
  };

  return (
    <div className="min-h-screen overflow-x-hidden bg-white text-[#263D3A] selection:bg-[#E4B45E]/30">
      <div className="relative z-50 flex min-h-10 items-center justify-center bg-[#8FD5E1] px-5 py-2 text-center text-[11px] font-bold uppercase tracking-[0.12em] text-[#164D59] sm:text-xs" data-testid="announcement-bar"><span>Private care for every chapter of her health · Tue · Thu · Sat</span></div>
      <header className="absolute inset-x-0 top-10 z-40 border-0 bg-transparent px-4 py-3 sm:px-6 lg:px-10" data-testid="site-header">
        <div className="mx-auto flex h-[4.5rem] max-w-7xl items-center justify-between rounded-sm bg-white px-5 shadow-[0_12px_35px_rgba(23,60,58,0.12)] sm:px-8 lg:px-6">
          <a href="#top" className="group flex items-center gap-3" data-testid="brand-home-link">
            <span className="size-11 overflow-hidden rounded-full border border-[#D9DFD4] bg-[#FFFDF8] shadow-sm transition-transform duration-300 group-hover:rotate-3"><img src={AMEYA_LOGO_URL} alt="Ameya Consultancy woman and leaf logo" className="size-full scale-125 object-cover" data-testid="header-brand-logo" /></span>
            <span><span className="block font-serif text-lg font-semibold leading-none text-[#164D59]" data-testid="brand-name">Ameya Consultancy</span><span className="mt-1 block text-[9px] font-semibold uppercase tracking-[0.22em] text-[#0E776C]" data-testid="brand-tagline">Her Health Connect</span></span>
          </a>
          <nav className="hidden items-center gap-7 lg:flex" aria-label="Main navigation" data-testid="desktop-navigation">
            {["Care pathways", "About Dr. Nisha", "Questions"].map((item, index) => <a key={item} href={`#${["care", "about", "faq"][index]}`} className="text-[13px] font-semibold text-[#35504D] transition-colors duration-300 hover:text-[#0E776C]" data-testid={`nav-${item.toLowerCase().replaceAll(" ", "-")}-link`}>{item}</a>)}
          </nav>
          <Button onClick={openBooking} className="h-10 rounded-sm bg-[#0E776C] px-5 text-sm text-white hover:bg-[#095D54]" data-testid="header-book-button">Book a consultation <ArrowUpRight className="ml-1.5 size-4" /></Button>
        </div>
      </header>

      <main id="top">
        <section className="relative min-h-[calc(100svh-2.5rem)] overflow-hidden bg-[#F4F1E8] px-5 pb-16 pt-40 sm:px-8 lg:px-12 lg:pb-20" data-testid="hero-section">
          <div className="absolute right-0 top-0 hidden h-full w-[39%] bg-[#0E776C] lg:block" aria-hidden="true" />
          <video src={HERO_VIDEO_URL} autoPlay={!reduceMotion} muted loop playsInline preload="metadata" className="absolute right-0 top-0 hidden h-full w-[39%] object-cover opacity-25 mix-blend-luminosity lg:block" aria-hidden="true" data-testid="hero-background-video" />
          <motion.div className="absolute -left-28 bottom-[-12rem] size-[28rem] rounded-full border-[1.5rem] border-[#E9B8AA]/60" aria-hidden="true" animate={reduceMotion ? undefined : { y: [0, -18, 0], rotate: [0, 5, 0] }} transition={{ duration: 14, repeat: Infinity, ease: "easeInOut" }} />
          <motion.div className="absolute right-[31%] top-[22%] hidden size-28 rounded-full bg-[#F6D776]/55 blur-sm lg:block" aria-hidden="true" animate={reduceMotion ? undefined : { y: [0, 24, 0], scale: [1, 1.08, 1] }} transition={{ duration: 11, repeat: Infinity, ease: "easeInOut" }} />
          <div className="relative z-10 mx-auto grid w-full max-w-7xl items-center gap-14 lg:grid-cols-[0.9fr_1.1fr] lg:gap-10">
            <Reveal className="relative z-10 max-w-2xl">
              <div className="mb-8 flex items-center gap-3 text-xs font-bold uppercase tracking-[0.2em] text-[#0E776C]" data-testid="hero-trust-pill"><span className="h-px w-10 bg-[#E07A5F]" /> Women’s health, personally held</div>
              <h1 className="max-w-2xl font-sans text-5xl font-medium leading-[0.96] tracking-[-0.055em] text-[#164D59] sm:text-7xl lg:text-[6.4rem]" data-testid="hero-heading">Care for every <span className="font-serif font-normal italic text-[#E07A5F]">stage</span> of womanhood.</h1>
              <p className="mt-8 max-w-xl text-lg leading-relaxed text-[#35504D] sm:text-xl" data-testid="hero-description">A calm, confidential place to ask the questions that change as you do—with <strong className="font-semibold text-[#164D59]">Dr. Nisha Ghelani</strong>, MD (Ob & Gyn), and 20+ years of experience.</p>
              <div className="mt-9 flex flex-col gap-3 sm:flex-row">
                <Button onClick={openBooking} className="h-13 rounded-sm bg-[#0E776C] px-6 text-base font-bold text-white shadow-[0_12px_24px_rgba(14,119,108,0.18)] hover:-translate-y-0.5 hover:bg-[#095D54]" data-testid="hero-book-button">Book a consultation <ArrowRight className="ml-2 size-4" /></Button>
                <a href="#care" className="inline-flex h-13 items-center justify-center rounded-sm border border-[#9EB9AD] px-6 text-base font-semibold text-[#164D59] transition-all duration-300 hover:-translate-y-0.5 hover:border-[#0E776C] hover:bg-white" data-testid="hero-care-link">See the care pathways</a>
              </div>
              <div className="mt-10 flex flex-wrap items-center gap-x-6 gap-y-3 border-t border-[#C9D3C6] pt-5 text-sm text-[#52706B]" data-testid="hero-contact-strip"><span className="flex items-center gap-2"><ShieldCheck className="size-4 text-[#0E776C]" /> Confidential by design</span><span className="flex items-center gap-2"><Clock3 className="size-4 text-[#0E776C]" /> Appointments · 10 AM–6 PM</span></div>
            </Reveal>
            <Reveal className="relative min-h-[34rem] sm:min-h-[38rem] lg:min-h-[42rem]" delay={0.12}>
              <motion.div className="absolute right-[7%] top-0 h-[78%] w-[66%] overflow-hidden rounded-t-[13rem] rounded-b-sm border-[10px] border-[#F4F1E8] bg-[#D7E5D7] shadow-[0_24px_50px_rgba(0,54,49,0.18)]" data-testid="hero-doctor-card" animate={reduceMotion ? undefined : { y: [0, -8, 0] }} transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}><img src={DR_NISHA_PORTRAIT_URL} alt="Dr. Nisha Ghelani in a white coat and stethoscope" className="h-full w-full object-cover object-[50%_18%]" fetchPriority="high" decoding="sync" data-testid="hero-doctor-image" /><div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-[#164D59]/85 to-transparent p-6 pt-20 text-white"><p className="font-serif text-2xl" data-testid="hero-doctor-name">Dr. Nisha Ghelani</p><p className="mt-1 text-xs font-semibold uppercase tracking-[0.16em] text-white/75" data-testid="hero-doctor-credential">MD (Ob & Gyn) · 20+ years</p></div></motion.div>
              <div className="absolute left-0 top-[17%] max-w-[11rem] bg-[#F6D776] p-5 text-[#164D59] shadow-[0_14px_30px_rgba(0,54,49,0.14)]" data-testid="hero-stage-card"><p className="font-mono text-[10px] font-bold uppercase tracking-[0.16em]">Every stage</p><p className="mt-3 font-serif text-2xl leading-tight">First periods to menopause.</p></div>
              <div className="absolute bottom-[9%] right-0 hidden max-w-[13rem] border border-white/45 bg-[#003F3A] p-5 text-white shadow-[0_14px_30px_rgba(0,54,49,0.18)] sm:block" data-testid="hero-experience-card"><p className="font-mono text-[10px] font-bold uppercase tracking-[0.16em] text-[#F6D776]">Her Health Connect</p><p className="mt-3 font-serif text-2xl leading-tight">20+ years of listening.</p><div className="mt-5 flex items-center gap-2 text-xs text-white/70"><HeartHandshake className="size-4 text-[#F6D776]" /> A space to be heard</div></div>
            </Reveal>
          </div>
        </section>

        <section className="hidden" aria-hidden="true" data-testid="legacy-care-photo-section">
          <div className="mx-auto max-w-7xl"><Reveal className="max-w-3xl"><p className="mb-5 text-xs font-bold uppercase tracking-[0.22em] text-[#F6D776]" data-testid="pathway-grid-eyebrow">Care that meets you where you are</p><h2 className="font-sans text-4xl font-medium leading-tight tracking-[-0.035em] sm:text-6xl" data-testid="pathway-grid-heading">Every chapter deserves its own kind of care.</h2><p className="mt-5 max-w-xl text-lg leading-relaxed text-white/70" data-testid="pathway-grid-copy">From first questions to second opinions, the right conversation can change how the next chapter feels.</p></Reveal><div className="mt-12 grid gap-3 sm:grid-cols-2 lg:grid-cols-4"><a href="#care" className="group relative aspect-[0.82] overflow-hidden rounded-sm bg-[#E5B4A9]" data-testid="pathway-card-antenatal"><img src="https://images.unsplash.com/photo-1749065306033-0cb90ff6e283?auto=format&fit=crop&w=900&q=85" alt="Antenatal consultation" className="absolute inset-0 h-full w-full object-cover transition-transform duration-700 group-hover:scale-105" /><div className="absolute inset-0 bg-gradient-to-t from-[#143F3B]/90 via-[#143F3B]/15 to-transparent" /><div className="absolute inset-x-5 bottom-5"><span className="font-mono text-[10px] uppercase tracking-[0.16em] text-[#F6D776]">01</span><h3 className="mt-2 font-serif text-2xl text-white">Antenatal care</h3><p className="mt-1 text-xs text-white/75">Pregnancy, with context.</p></div></a><a href="#care" className="group relative aspect-[0.82] overflow-hidden rounded-sm bg-[#8FD5E1]" data-testid="pathway-card-postnatal"><img src="https://images.unsplash.com/photo-1702788177324-3a4925d4f4cf?auto=format&fit=crop&w=900&q=85" alt="Postnatal mother and baby care" className="absolute inset-0 h-full w-full object-cover transition-transform duration-700 group-hover:scale-105" /><div className="absolute inset-0 bg-gradient-to-t from-[#143F3B]/90 via-[#143F3B]/15 to-transparent" /><div className="absolute inset-x-5 bottom-5"><span className="font-mono text-[10px] uppercase tracking-[0.16em] text-[#F6D776]">02</span><h3 className="mt-2 font-serif text-2xl text-white">Postnatal care</h3><p className="mt-1 text-xs text-white/75">Care for the person, too.</p></div></a><a href="#care" className="group relative aspect-[0.82] overflow-hidden rounded-sm bg-[#E9D277]" data-testid="pathway-card-puberty"><img src="https://images.unsplash.com/photo-1638202993928-7267aad84c31?auto=format&fit=crop&w=900&q=85" alt="Warm women's health clinic" className="absolute inset-0 h-full w-full object-cover transition-transform duration-700 group-hover:scale-105" /><div className="absolute inset-0 bg-gradient-to-t from-[#143F3B]/90 via-[#143F3B]/15 to-transparent" /><div className="absolute inset-x-5 bottom-5"><span className="font-mono text-[10px] uppercase tracking-[0.16em] text-[#F6D776]">03</span><h3 className="mt-2 font-serif text-2xl text-white">Puberty & cycles</h3><p className="mt-1 text-xs text-white/75">Private questions welcome.</p></div></a><a href="#care" className="group relative aspect-[0.82] overflow-hidden rounded-sm bg-[#B7D5C7]" data-testid="pathway-card-menopause"><img src="https://images.pexels.com/photos/6749765/pexels-photo-6749765.jpeg?auto=compress&cs=tinysrgb&w=900" alt="Doctor ready to listen" className="absolute inset-0 h-full w-full object-cover transition-transform duration-700 group-hover:scale-105" /><div className="absolute inset-0 bg-gradient-to-t from-[#143F3B]/90 via-[#143F3B]/15 to-transparent" /><div className="absolute inset-x-5 bottom-5"><span className="font-mono text-[10px] uppercase tracking-[0.16em] text-[#F6D776]">04</span><h3 className="mt-2 font-serif text-2xl text-white">Menopause & more</h3><p className="mt-1 text-xs text-white/75">A new rhythm, supported.</p></div></a></div></div>
        </section>

        <section className="bg-[#003F3A] px-5 py-24 text-white sm:px-8 lg:px-12 lg:py-32" data-testid="care-stories-section">
          <div className="mx-auto max-w-7xl"><Reveal className="grid gap-8 lg:grid-cols-[1fr_0.7fr] lg:items-end"><div><p className="mb-5 text-xs font-bold uppercase tracking-[0.22em] text-[#F6D776]" data-testid="care-stories-eyebrow">Care across womanhood</p><h2 className="font-sans text-4xl font-medium leading-tight tracking-[-0.035em] sm:text-6xl" data-testid="care-stories-heading">Expertise for the chapter you are in.</h2></div><p className="max-w-xl text-lg leading-relaxed text-white/70" data-testid="care-stories-copy">Each pathway begins with a private conversation—not a one-size-fits-all plan.</p></Reveal><div className="mt-14 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">{careStories.map((story) => <button key={story.id} type="button" onClick={() => { setActiveFocus(story.id); document.getElementById("care")?.scrollIntoView({ behavior: "smooth" }); }} className="group overflow-hidden rounded-[1.4rem] bg-white text-left shadow-[0_18px_45px_rgba(0,20,18,0.2)] transition-transform duration-300 hover:-translate-y-1" data-testid={`care-story-${story.id}`}><div className="aspect-[1.05] overflow-hidden bg-[#DCEBE6]"><img src={story.image} alt={story.title} className="h-full w-full object-cover transition-transform duration-700 group-hover:scale-105" /></div><div className="min-h-40 bg-[#FFFDF8] p-5 text-[#164D59]"><span className="font-mono text-[10px] font-bold tracking-[0.16em] text-[#E07A5F]">{story.number}</span><h3 className="mt-3 font-serif text-2xl">{story.title}</h3><p className="mt-2 text-sm leading-relaxed text-[#52706B]">{story.note}</p><span className="mt-4 inline-flex items-center gap-1 text-xs font-bold text-[#0E776C]">Explore pathway <ArrowUpRight className="size-3.5" /></span></div></button>)}</div></div>
        </section>

        <section id="about" className="bg-[#F4F1E8] px-5 py-24 sm:px-8 lg:px-12 lg:py-32" data-testid="about-section">
          <div className="mx-auto max-w-7xl"><div className="grid gap-14 lg:grid-cols-[0.8fr_1.2fr] lg:gap-24"><Reveal><p className="mb-5 text-xs font-bold uppercase tracking-[0.22em] text-[#0E776C]" data-testid="about-eyebrow">Meet your doctor</p><h2 className="max-w-sm font-sans text-4xl font-medium leading-tight tracking-[-0.035em] text-[#164D59] sm:text-6xl" data-testid="about-heading">Medicine begins with feeling heard.</h2></Reveal><Reveal className="max-w-2xl" delay={0.1}><p className="text-xl leading-relaxed text-[#35504D]" data-testid="about-intro">Dr. Nisha Ghelani believes a consultation should leave you with more than a prescription. It should leave you with clarity, a plan, and the confidence to ask the next question.</p><div className="mt-10 grid gap-8 border-t border-[#C9D3C6] pt-8 sm:grid-cols-3"><div data-testid="about-stat-experience"><span className="font-serif text-5xl text-[#0E776C]">20+</span><span className="mt-2 block text-xs font-bold uppercase tracking-[0.14em] text-[#35504D]">Years of experience</span></div><div data-testid="about-stat-approach"><span className="font-serif text-5xl text-[#0E776C]">1:1</span><span className="mt-2 block text-xs font-bold uppercase tracking-[0.14em] text-[#35504D]">Personal attention</span></div><div data-testid="about-stat-care"><span className="font-serif text-5xl text-[#0E776C]">100%</span><span className="mt-2 block text-xs font-bold uppercase tracking-[0.14em] text-[#35504D]">Confidential care</span></div></div></Reveal></div>
          <Reveal className="mt-14 grid overflow-hidden rounded-[1.5rem] bg-white shadow-[0_20px_60px_rgba(22,77,89,0.08)] lg:grid-cols-[1.15fr_0.85fr]" delay={0.08}><div className="min-h-72 overflow-hidden lg:min-h-[24rem]"><img src={DR_NISHA_DELIVERY_URL} alt="Dr. Nisha caring for a newborn in the delivery room" className="h-full w-full object-cover" data-testid="doctor-clinical-care-image" /></div><div className="flex flex-col justify-center p-7 sm:p-10 lg:p-12"><p className="text-xs font-bold uppercase tracking-[0.2em] text-[#E07A5F]" data-testid="doctor-clinical-label">Experience in action</p><h3 className="mt-5 font-serif text-3xl leading-tight text-[#164D59]" data-testid="doctor-clinical-heading">Clinical confidence, with human warmth.</h3><p className="mt-5 text-sm leading-relaxed text-[#52706B]" data-testid="doctor-clinical-copy">More than two decades across pregnancy, childbirth, recovery, adolescence and menopause inform every conversation—without ever losing sight of the person behind the report.</p></div></Reveal>
          <Reveal className="mx-auto mt-16 grid max-w-7xl items-end gap-8 rounded-sm bg-[#0E776C] p-7 text-white sm:p-10 lg:grid-cols-[1fr_0.65fr] lg:p-14" delay={0.08}><div><p className="text-xs font-bold uppercase tracking-[0.2em] text-[#F6D776]" data-testid="philosophy-label">Her care philosophy</p><blockquote className="mt-5 max-w-2xl font-serif text-3xl leading-tight sm:text-4xl" data-testid="philosophy-quote">“There is no small question when it comes to your health. We make time for all of them.”</blockquote></div><div className="border-t border-white/20 pt-6 lg:border-l lg:border-t-0 lg:pl-8 lg:pt-0"><p className="text-sm leading-relaxed text-white/75" data-testid="philosophy-copy">Whether you are preparing for motherhood, finding your footing after birth, navigating a new stage, or simply seeking another perspective—this is a place to pause and talk it through.</p></div></Reveal></div>
        </section>

        <section id="care" className="bg-[#8FD5E1]" data-testid="care-section"><div className="mx-auto max-w-7xl px-5 py-24 sm:px-8 lg:px-12 lg:py-32"><Reveal className="max-w-2xl"><p className="mb-5 text-xs font-bold uppercase tracking-[0.22em] text-[#0E776C]" data-testid="care-eyebrow">Care pathways</p><h2 className="font-sans text-4xl font-medium leading-tight tracking-[-0.035em] text-[#164D59] sm:text-6xl" data-testid="care-heading">The right conversation for where you are.</h2><p className="mt-5 text-lg leading-relaxed text-[#35504D]" data-testid="care-intro">Choose a pathway to see how Dr. Nisha can support you—with expertise, context, and no rush.</p></Reveal><div className="mt-12 grid gap-10 lg:grid-cols-[0.42fr_0.58fr] lg:gap-20"><div className="flex flex-col gap-2" role="tablist" aria-label="Care pathways" data-testid="care-pathway-tabs">{focusAreas.map((area, index) => <button key={area.id} role="tab" aria-selected={activeFocus === area.id} onClick={() => setActiveFocus(area.id)} className={`group flex items-center justify-between border-b px-1 py-4 text-left transition-colors duration-300 ${activeFocus === area.id ? "border-[#164D59] text-[#164D59]" : "border-[#5FB5B7]/60 text-[#35504D] hover:text-[#164D59]"}`} data-testid={`care-tab-${area.id}`}><span className="flex items-center gap-4"><span className={`font-mono text-xs ${activeFocus === area.id ? "text-[#0E776C]" : "text-[#35504D]"}`}>0{index + 1}</span><span className="font-serif text-xl">{area.title}</span></span><ArrowUpRight className={`size-4 transition-transform duration-300 ${activeFocus === area.id ? "translate-x-1 -translate-y-1 text-[#0E776C]" : "opacity-0 group-hover:opacity-100"}`} /></button>)}</div><motion.div key={activeArea.id} initial={{ opacity: 0, x: 12 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.4 }} className="rounded-sm border border-white/70 bg-white p-7 shadow-[0_18px_50px_rgba(22,77,89,0.12)] sm:p-10" role="tabpanel" data-testid="care-pathway-panel"><div className="flex items-center justify-between"><Badge className="border-[#C8E3DB] bg-[#EAF2F1] text-[#0E776C]" data-testid="care-pathway-eyebrow">{activeArea.eyebrow}</Badge><span className="font-mono text-xs text-[#35504D]" data-testid="care-pathway-id">{activeArea.id}</span></div><h3 className="mt-8 max-w-lg font-serif text-3xl leading-tight text-[#164D59] sm:text-4xl" data-testid="care-pathway-heading">{activeArea.heading}</h3><p className="mt-5 max-w-xl text-base leading-relaxed text-[#35504D]" data-testid="care-pathway-description">{activeArea.body}</p><ul className="mt-8 grid gap-3 sm:grid-cols-2" data-testid="care-pathway-points">{activeArea.points.map((point) => <li key={point} className="flex items-center gap-2 text-sm text-[#263D3A]"><Check className="size-4 text-[#E07A5F]" /> {point}</li>)}</ul><Button onClick={scrollToBooking} className="mt-10 rounded-sm bg-[#0E776C] text-white hover:bg-[#095D54]" data-testid="care-pathway-book-button">Book this pathway <ArrowRight className="ml-2 size-4" /></Button></motion.div></div></div></section>

        <section className="bg-[#F6D776] px-5 py-20 sm:px-8 lg:px-12 lg:py-24" data-testid="booking-cta-section"><Reveal className="mx-auto grid max-w-7xl gap-8 lg:grid-cols-[1fr_0.65fr] lg:items-center"><div><p className="text-xs font-bold uppercase tracking-[0.2em] text-[#0E776C]" data-testid="booking-cta-eyebrow">Ready when you are</p><h2 className="mt-5 max-w-3xl font-sans text-4xl font-medium leading-tight tracking-[-0.04em] text-[#164D59] sm:text-6xl" data-testid="booking-cta-heading">Choose a private Google Meet time that works for you.</h2></div><div className="flex flex-col gap-3 sm:flex-row lg:flex-col"><Button onClick={openBooking} className="h-14 rounded-full bg-[#0E776C] px-7 text-base font-bold text-white hover:bg-[#095D54]" data-testid="booking-cta-button"><CalendarDays className="mr-2 size-5" /> Book a consultation</Button><a href={WHATSAPP_URL} target="_blank" rel="noreferrer" className="inline-flex h-14 items-center justify-center rounded-full border border-[#164D59]/30 px-7 text-base font-bold text-[#164D59] transition-colors duration-200 hover:bg-white/60" data-testid="booking-cta-whatsapp"><MessageCircle className="mr-2 size-5" /> Ask on WhatsApp</a></div></Reveal></section>


        <section id="faq" className="mx-auto max-w-7xl px-5 py-24 sm:px-8 lg:px-12 lg:py-32" data-testid="faq-section"><div className="grid gap-12 lg:grid-cols-[0.7fr_1.3fr] lg:gap-24"><Reveal><p className="mb-5 text-xs font-bold uppercase tracking-[0.22em] text-[#E07A5F]" data-testid="faq-eyebrow">A few answers</p><h2 className="font-serif text-4xl leading-tight text-[#114B5F] sm:text-5xl" data-testid="faq-heading">Before we meet.</h2><p className="mt-5 max-w-sm text-lg leading-relaxed text-[#5C6479]" data-testid="faq-intro">Good care starts with clarity. Here are a few things patients often want to know.</p></Reveal><Reveal className="divide-y divide-[#E5DEC9] border-y border-[#E5DEC9]" delay={0.1}>{faqs.map((faq, index) => <div key={faq.question} data-testid={`faq-item-${index + 1}`}><button type="button" aria-expanded={openFaq === index} onClick={() => setOpenFaq(openFaq === index ? -1 : index)} className="flex min-h-16 w-full items-center justify-between gap-5 py-5 text-left font-serif text-xl text-[#114B5F]" data-testid={`faq-question-${index + 1}`}>{faq.question}<ChevronDown className={`size-5 shrink-0 text-[#E07A5F] transition-transform duration-300 ${openFaq === index ? "rotate-180" : ""}`} /></button>{openFaq === index && <p className="max-w-2xl pb-6 pr-8 text-sm leading-relaxed text-[#5C6479]" data-testid={`faq-answer-${index + 1}`}>{faq.answer}</p>}</div>)}</Reveal></div></section>
      </main>

      <footer className="bg-[#114B5F] text-white" data-testid="site-footer"><div className="mx-auto max-w-7xl px-5 py-12 sm:px-8 lg:px-12"><div className="grid gap-10 border-b border-white/15 pb-10 lg:grid-cols-[1.2fr_0.8fr_0.8fr]"><div><div className="flex items-center gap-3"><span className="size-14 overflow-hidden rounded-full border border-white/20 bg-[#FFFDF8]"><img src={AMEYA_LOGO_URL} alt="Ameya Consultancy woman and leaf logo" className="size-full scale-125 object-cover" data-testid="footer-brand-logo" /></span><span className="font-serif text-xl" data-testid="footer-brand">Ameya Consultancy</span></div><p className="mt-5 max-w-sm text-sm leading-relaxed text-white/65" data-testid="footer-description">Her Health Connect—a private space for expert women's health conversations with Dr. Nisha Ghelani.</p></div><div><p className="text-xs font-bold uppercase tracking-[0.18em] text-[#F4C2B4]" data-testid="footer-contact-label">Contact</p><div className="mt-4 space-y-3 text-sm text-white/75"><a href="tel:+916355734167" className="flex items-center gap-2 hover:text-white" data-testid="footer-phone-link"><Phone className="size-4" /> +91 63557 34167</a><a href="mailto:nishaghelani78@gmail.com" className="flex items-center gap-2 break-all hover:text-white" data-testid="footer-email-link"><Mail className="size-4" /> nishaghelani78@gmail.com</a></div></div><div><p className="text-xs font-bold uppercase tracking-[0.18em] text-[#F4C2B4]" data-testid="footer-availability-label">Availability</p><p className="mt-4 text-sm leading-relaxed text-white/75" data-testid="footer-availability-copy">Tuesday, Thursday & Saturday<br />By appointment only</p><Button onClick={scrollToBooking} variant="outline" className="mt-5 rounded-full border-white/30 bg-transparent text-white hover:bg-white hover:text-[#114B5F]" data-testid="footer-book-button">Request a time <ArrowUpRight className="ml-1.5 size-4" /></Button></div></div><div className="mt-8 rounded-2xl border border-[#F4C2B4]/35 bg-[#0d3b4b] p-5" data-testid="statutory-notice"><p className="text-xs font-bold uppercase tracking-[0.18em] text-[#F4C2B4]">Important care notice</p><p className="mt-2 max-w-3xl text-sm leading-relaxed text-white/75">Ameya Consultancy is for planned consultations and expert advice. It is not an emergency service. For acute pain, heavy bleeding, breathing difficulty, or any obstetric emergency, please contact your nearest hospital emergency department immediately.</p></div><p className="mt-8 text-xs text-white/45" data-testid="footer-copyright">© {new Date().getFullYear()} Ameya Consultancy · Dr. Nisha Ghelani, MD (Ob & Gyn)</p></div></footer>

      <a href={WHATSAPP_URL} target="_blank" rel="noreferrer" className="fixed bottom-20 right-4 z-40 flex size-14 items-center justify-center rounded-full bg-[#1FAF62] text-white shadow-[0_12px_30px_rgba(31,175,98,0.3)] transition-transform duration-200 hover:-translate-y-1 md:bottom-6 md:right-6" aria-label="Chat with Dr. Nisha on WhatsApp" data-testid="floating-whatsapp-button"><MessageCircle className="size-6" /></a>
      <div className="fixed inset-x-0 bottom-0 z-50 grid grid-cols-2 gap-2 border-t border-[#E5DEC9] bg-[#FAF8F5]/95 p-3 shadow-[0_-10px_30px_rgba(17,75,95,0.12)] backdrop-blur-md md:hidden" data-testid="mobile-quick-action-bar"><a href="tel:+916355734167" className="flex min-h-12 items-center justify-center gap-2 rounded-full border border-[#114B5F] bg-transparent text-sm font-semibold text-[#114B5F]" data-testid="mobile-call-doctor-button"><Phone className="size-4" /> Call doctor</a><Button onClick={openBooking} className="min-h-12 rounded-full bg-[#E07A5F] text-sm text-white hover:bg-[#c9654c]" data-testid="mobile-book-button"><CalendarDays className="mr-2 size-4" /> Book consultation</Button></div>

      <Dialog open={bookingOpen} onOpenChange={setBookingOpen}><DialogContent className="left-0 top-auto bottom-0 max-h-[94vh] w-full max-w-none translate-x-0 translate-y-0 overflow-y-auto rounded-b-none rounded-t-[2rem] border-[#D9DFD4] bg-[#FFFDF8] p-5 sm:p-8 md:left-[50%] md:top-[50%] md:bottom-auto md:max-w-5xl md:translate-x-[-50%] md:translate-y-[-50%] md:rounded-[2rem]" data-testid="appointment-booking-dialog"><DialogHeader><DialogTitle className="font-serif text-3xl text-[#164D59]" data-testid="appointment-booking-title">Book a Google Meet consultation</DialogTitle><DialogDescription data-testid="appointment-booking-description">Choose your care, date, and exact time. Attach reports if helpful.</DialogDescription></DialogHeader><div className="mt-5"><BookingForm onCreated={handleCreated} testIdPrefix="appointment" /></div></DialogContent></Dialog>
      <Dialog open={confirmationOpen} onOpenChange={setConfirmationOpen}><DialogContent className="max-w-md border-[#E5DEC9] bg-[#FAF8F5]" data-testid="appointment-confirmation-dialog"><DialogHeader><div className="mb-3 flex size-12 items-center justify-center rounded-full bg-[#D6E1DC] text-[#1A5E72]"><Check className="size-6" /></div><DialogTitle className="font-serif text-3xl text-[#114B5F]" data-testid="confirmation-title">Your appointment is saved.</DialogTitle><DialogDescription className="text-base leading-relaxed" data-testid="confirmation-description">Thank you, {confirmedAppointment?.full_name}. Your preferred time is saved for Dr. Nisha.</DialogDescription></DialogHeader><div className="mt-5 rounded-xl border border-[#E5DEC9] bg-white p-4" data-testid="confirmation-reference-card"><p className="text-xs font-bold uppercase tracking-[0.16em] text-[#839788]">Booking reference</p><p className="mt-1 font-mono text-xl font-semibold text-[#114B5F]" data-testid="confirmation-reference">{confirmedAppointment?.reference}</p><p className="mt-3 text-sm text-[#5C6479]" data-testid="confirmation-meet-status">{confirmedAppointment?.meeting_status === "scheduled" ? "Your Google Meet link is ready and will be emailed to you." : "Google Calendar is not connected yet, so a Meet link could not be created. Dr. Nisha will follow up directly."}</p></div><p className="mt-5 text-sm leading-relaxed text-[#5C6479]" data-testid="confirmation-privacy-copy">Your reports and details remain private and are used only for this appointment.</p></DialogContent></Dialog>
    </div>
  );
}