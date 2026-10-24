import { ApiError } from "@/lib/api";
import { KEYWORD_MENTORS, MENTORS } from "@/mocks/data";
import type {
  AdminSummary, Booking, ChatReply, ChatTranscript, ErrorCode, Match, MentorFilters, PublicMentor, Reason, Slot, Student,
  Writeup,
} from "@/lib/types";

/*
 * In-browser mock of the contract. Stateful parts (students, chats, bookings)
 * persist to localStorage so a reload keeps the demo going.
 *
 * Triggers for the demo, all by keyword in the chat message:
 *   fewer than 5 words ........ clarify (up to 3 times per session)
 *   "poem", "joke", "weather" . redirect (off topic)
 *   "depressed", "suicide" .... redirect (sensitive, points to help)
 *   "astronaut", "plumber" .... no_match
 *   anything else ............. matches (keywords pick the mentors)
 * Booking triggers:
 *   the first slot on day 1 of every mentor ... slot_taken
 *   mentor M007 ............................... mentor_cap_reached
 *   a 4th active booking ...................... booking_cap_reached
 * Admin password: mesa-admin
 */

export const MOCK_ADMIN_PASSWORD = "mesa-admin";

type Db = {
  students: Student[];
  bookings: (Booking & { token: string; notes?: string })[];
  taken: string[];
  sessions: Record<string, { messages: ChatTranscript["messages"]; clarify: number; last: ChatReply | null; student: string | null }>;
  unmatched: { id: string; created_at: string; summary: string }[];
  writeups: Record<string, Writeup>;
};

const KEY = "mc_mock_db";
let memory: Db = empty();

function empty(): Db {
  return { students: [], bookings: [], taken: [], sessions: {}, unmatched: [], writeups: {} };
}

function load(): Db {
  if (typeof window === "undefined") return memory;
  try {
    const raw = window.localStorage.getItem(KEY);
    if (raw) memory = JSON.parse(raw) as Db;
  } catch {
    // keep in-memory copy
  }
  return memory;
}

function save(db: Db) {
  memory = db;
  try {
    window.localStorage.setItem(KEY, JSON.stringify(db));
  } catch {
    // storage unavailable: memory only
  }
}

const err = (code: ErrorCode, message: string): never => {
  const status = { validation_error: 422, not_found: 404, unauthorized: 401, ai_unavailable: 503 }[code as string] ?? 409;
  throw new ApiError(code, message, status);
};

const wait = (ms = 250) => new Promise((r) => setTimeout(r, ms));
const uid = (p: string) => `${p}_${Math.random().toString(36).slice(2, 9)}`;

// ---------- slots ----------
const HOURS_UTC = [[4, 30], [9, 30], [12, 30]]; // 10:00, 15:00, 18:00 IST

function slotsFor(mentorId: string, db: Db): Slot[] {
  const base = new Date();
  base.setUTCHours(0, 0, 0, 0);
  const out: Slot[] = [];
  for (let d = 1; d <= 7; d++) {
    HOURS_UTC.forEach(([h, m], t) => {
      const start = new Date(base.getTime() + d * 86400000);
      start.setUTCHours(h, m);
      const id = `${mentorId}-d${d}-t${t}`;
      if (db.taken.includes(id)) return;
      out.push({ id, mentor_id: mentorId, start: start.toISOString(), end: new Date(start.getTime() + 1800000).toISOString(), status: "open" });
    });
  }
  return out;
}

// ---------- chat ----------
const FIELD_LABEL_VALUE: Record<string, (m: PublicMentor) => string | null> = {
  domain: (m) => m.domain,
  sector: (m) => m.sector,
  company: (m) => m.company,
  city: (m) => m.city,
  seniority: (m) => m.seniority,
  quality: (m) => m.quality,
  sectors: (m) => (m.sectors.length ? m.sectors.join(", ") : null),
  roles: (m) => (m.roles.length ? m.roles.join(", ") : null),
  tools: (m) => {
    const on = Object.entries(m.tools).filter(([, v]) => v).map(([k]) => k.replace("_", " "));
    return on.length ? on.join(", ") : null;
  },
  built_ai: (m) => (m.built_ai === null ? null : m.built_ai ? "Yes" : "No"),
};

const REASON_TEXT: Record<string, string> = {
  domain: "Works in the area you described.",
  sector: "Knows the sector you are aiming for.",
  sectors: "Has covered these sectors with students.",
  roles: "Has held the kind of role you are asking about.",
  tools: "Uses tools you mentioned.",
  built_ai: "Has hands-on experience with AI products.",
  seniority: "Can speak to how this career path moves.",
  company: "Works at a company in your target space.",
};

function reasonsFor(m: PublicMentor, fields: string[]): Reason[] {
  const out: Reason[] = [];
  for (const f of [...fields, "quality", "company"]) {
    const value = FIELD_LABEL_VALUE[f]?.(m);
    if (value && !out.some((r) => r.field === f)) out.push({ field: f, value, text: REASON_TEXT[f] ?? "Rated well by earlier students." });
    if (out.length === 3) break;
  }
  return out;
}

function reply(db: Db, sid: string, text: string): ChatReply {
  const s = db.sessions[sid];
  const words = text.trim().split(/\s+/).length;
  const base = { session_id: sid, matches: [] as Match[], need: null };

  if (/depress|suicid|self.?harm|hopeless/i.test(text)) {
    return { ...base, kind: "redirect", message: "That sounds heavy, and a mentor call is not the right place for it. Please talk to someone you trust, or call the Tele-MANAS helpline at 14416. When you want to work on career questions, I am here." };
  }
  if (/poem|joke|weather|recipe|movie|cricket score/i.test(text)) {
    return { ...base, kind: "redirect", message: "I can only help with career questions. Tell me what you are stuck on, such as choosing a field, a first job, or a skill to build." };
  }
  if (/astronaut|plumber|deep sea/i.test(text)) {
    db.unmatched.unshift({ id: uid("U"), created_at: new Date().toISOString(), summary: text.slice(0, 120) });
    return {
      ...base, kind: "no_match",
      message: "None of our 50 mentors work in that area, so I won't guess. I have noted it for the Mesa team. You can browse all mentors or describe a different goal.",
      need: { summary: text.slice(0, 120), domains: [], sectors: [], tools: [], wants_ai: false },
    };
  }
  if (words < 5 && s.clarify < 3) {
    s.clarify += 1;
    return { ...base, kind: "clarify", message: s.clarify === 1 ? "Can you say more? For example, what are you studying, and what do you want to be doing in two years?" : "Almost there. Which kind of work are you curious about, and what is holding you back?" };
  }
  const rule = KEYWORD_MENTORS.find((r) => r.words.test(text)) ?? KEYWORD_MENTORS[0];
  const matches: Match[] = rule.ids.map((id) => {
    const mentor = MENTORS.find((m) => m.id === id)!;
    return { mentor, reasons: reasonsFor(mentor, rule.reasonFields) };
  });
  return {
    ...base, kind: "matches",
    message: "Here are three mentors whose profiles fit what you described. Each reason below is a value taken from their profile.",
    matches,
    need: { summary: text.slice(0, 140), domains: [matches[0].mentor.domain], sectors: matches[0].mentor.sector ? [matches[0].mentor.sector] : [], tools: [], wants_ai: /\bai\b/i.test(text) },
  };
}

// ---------- write-up ----------
function writeupFrom(notes: string): Writeup {
  const parts = notes.split(/(?<=[.!?\n])\s+/).map((p) => p.trim()).filter(Boolean);
  const third = Math.max(1, Math.ceil(parts.length / 3));
  return {
    status: "ready",
    discussed: parts.slice(0, third),
    work_on: parts.slice(third, third * 2).length ? parts.slice(third, third * 2) : ["Pick one area from the call and spend an hour on it this week."],
    next_steps: parts.slice(third * 2).length ? parts.slice(third * 2) : ["Book a follow-up once you have tried the first step."],
  };
}

// ---------- router ----------
function findMentor(id: string): PublicMentor {
  return MENTORS.find((m) => m.id === id) ?? err("not_found", "We could not find that mentor.");
}

function filterMentors(f: MentorFilters): PublicMentor[] {
  const q = f.q?.toLowerCase();
  return MENTORS.filter(
    (m) =>
      (!f.domain || m.domain === f.domain) &&
      (!f.sector || m.sector === f.sector || m.sectors.includes(f.sector)) &&
      (!f.city || m.city === f.city) &&
      (!q || [m.name, m.domain, m.company ?? "", m.sector ?? "", ...m.roles, ...m.sectors].join(" ").toLowerCase().includes(q)),
  );
}

// Student views carry the demo mentor token; the mentor page and admin do not.
function stripToken(b: Booking & { token?: string; notes?: string }, withToken = true): Booking {
  const { token, notes: _n, ...rest } = b;
  void _n;
  return { ...rest, mentor_token: withToken ? (token ?? null) : null };
}

function mine(db: Db, studentId: string | undefined): Db["bookings"] {
  if (!studentId) err("validation_error", "Sign in with your name and email first.");
  return db.bookings.filter((b) => b.student_id === studentId);
}

function seedAdmin(db: Db): AdminSummary {
  const by = { confirmed: 0, completed: 0, no_show: 0, cancelled: 0 };
  db.bookings.forEach((b) => (by[b.status] += 1));
  const load: Record<string, { mentor_id: string; name: string; active: number; completed: number }> = {};
  db.bookings.forEach((b) => {
    load[b.mentor.id] ??= { mentor_id: b.mentor.id, name: b.mentor.name, active: 0, completed: 0 };
    if (b.status === "confirmed") load[b.mentor.id].active += 1;
    if (b.status === "completed") load[b.mentor.id].completed += 1;
  });
  const old = new Date(Date.now() - 4 * 86400000).toISOString();
  const stuck: Booking = {
    id: "B-seed-stuck", student_id: "S-seed", mentor: MENTORS[1], brief: "Wants to move from operations into data analytics.",
    slot: { id: "seed", mentor_id: "M007", start: old, end: old, status: "booked" }, status: "confirmed", created_at: old, writeup_status: "none", mentor_token: null,
  };
  return {
    funnel: {
      chats_started: 48 + Object.keys(db.sessions).length, matched: 39 + db.bookings.length, booked: 21 + db.bookings.length,
      completed: 14 + by.completed, writeups_ready: 12, rebooked: 3,
    },
    bookings_by_status: { confirmed: 5 + by.confirmed, completed: 14 + by.completed, no_show: 2 + by.no_show, cancelled: 1 + by.cancelled },
    stuck: [stuck],
    unmatched: [
      ...db.unmatched,
      { id: "U-seed", created_at: old, summary: "Wants to become a marine biologist in Goa" },
    ],
    mentor_load: [{ mentor_id: "M003", name: "Asha Raman", active: 2, completed: 6 }, ...Object.values(load)],
  };
}

export async function mockRequest<T>(
  method: "GET" | "POST",
  path: string,
  body: unknown,
  headers: Record<string, string>,
): Promise<T> {
  await wait();
  const [route, query = ""] = path.split("?");
  const seg = route.split("/").filter(Boolean).map(decodeURIComponent);
  const b = (body ?? {}) as Record<string, string>;
  const db = load();
  const sid = headers["X-Student-Id"];
  const result = (v: unknown) => v as T;

  if (seg[0] === "mentors") {
    if (seg.length === 1) {
      const p = new URLSearchParams(query);
      return result(filterMentors({ q: p.get("q") ?? undefined, domain: p.get("domain") ?? undefined, sector: p.get("sector") ?? undefined, city: p.get("city") ?? undefined }));
    }
    if (seg[2] === "slots") {
      findMentor(seg[1]);
      return result(slotsFor(seg[1], db));
    }
    return result(findMentor(seg[1]));
  }

  if (seg[0] === "students" && method === "POST") {
    if (!b.name?.trim() || !/^\S+@\S+\.\S+$/.test(b.email ?? "")) err("validation_error", "Enter your name and a valid email address.");
    let s = db.students.find((x) => x.email === b.email.toLowerCase());
    if (!s) {
      s = { id: uid("S"), name: b.name.trim(), email: b.email.toLowerCase() };
      db.students.push(s);
      save(db);
    }
    return result(s);
  }

  if (seg[0] === "contact" && method === "POST") {
    if (!b.name?.trim() || !/^\S+@\S+\.\S+$/.test(b.email ?? "") || !b.message?.trim()) err("validation_error", "Enter your name, a valid email and a message.");
    return result({ id: uid("C"), status: "received" });
  }

  if (seg[0] === "chat") {
    if (method === "GET") {
      const s = db.sessions[seg[1]] ?? err("not_found", "We could not find that chat.");
      return result({ messages: s.messages, last: s.last });
    }
    const text = (b.message ?? "").trim();
    if (!text || text.length > 2000) err("validation_error", "Write between 1 and 2000 characters.");
    const id = b.session_id ?? uid("C");
    db.sessions[id] ??= { messages: [], clarify: 0, last: null, student: sid ?? null };
    const r = reply(db, id, text);
    db.sessions[id].messages.push({ role: "student", text }, { role: "assistant", text: r.message });
    db.sessions[id].last = r;
    save(db);
    return result(r);
  }

  if (seg[0] === "bookings") {
    if (seg.length === 1 && method === "GET") return result(mine(db, sid).map((x) => stripToken(x)));
    if (seg.length === 1) {
      const list = mine(db, sid);
      const mentor = findMentor(b.mentor_id);
      if (mentor.id === "M007") err("mentor_cap_reached", "This mentor is fully booked this week. Pick another mentor or try next week.");
      if (list.filter((x) => x.status === "confirmed").length >= 3) err("booking_cap_reached", "You have 3 upcoming calls already. Finish or cancel one to book another.");
      const slot = slotsFor(mentor.id, db).find((s) => s.id === b.slot_id);
      if (!slot || b.slot_id.endsWith("-d1-t0")) {
        db.taken.push(b.slot_id);
        save(db);
        err("slot_taken", "That slot was just booked. Pick another time.");
      }
      const chat = db.sessions[b.session_id]?.last?.need?.summary;
      const booking = {
        id: uid("B"), student_id: sid!, mentor, slot: { ...slot!, status: "booked" as const }, status: "confirmed" as const,
        brief: chat ?? "Student wants advice on getting started in this field.", created_at: new Date().toISOString(),
        writeup_status: "none" as const, mentor_token: null, token: uid("tok"),
      };
      db.bookings.push(booking);
      db.taken.push(slot!.id);
      save(db);
      return result(stripToken(booking));
    }
    const bk = mine(db, sid).find((x) => x.id === seg[1]) ?? err("not_found", "We could not find that booking.");
    if (seg[2] === "cancel") {
      if (bk.status !== "confirmed") err("invalid_state", "Only upcoming calls can be cancelled.");
      bk.status = "cancelled";
      db.taken = db.taken.filter((t) => t !== bk.slot.id);
      save(db);
    }
    if (seg[2] === "writeup") return result(db.writeups[bk.id] ?? { status: bk.writeup_status, discussed: [], work_on: [], next_steps: [] });
    return result(stripToken(bk));
  }

  if (seg[0] === "m") {
    const bk = db.bookings.find((x) => x.token === seg[1]) ?? err("not_found", "This mentor link is not valid. Ask the student to share it again.");
    const studentName = db.students.find((s) => s.id === bk.student_id)?.name ?? "Student";
    if (!seg[2]) return result({ booking: stripToken(bk, false), student_name: studentName });
    const notes = (b.notes ?? "").trim();
    if (seg[2] === "close") {
      if (bk.status !== "confirmed") err("invalid_state", "This call is already closed.");
      if (b.outcome !== "completed" && b.outcome !== "no_show") err("validation_error", "Choose completed or no-show.");
      bk.status = b.outcome as "completed" | "no_show";
      if (b.outcome === "completed" && notes) {
        bk.writeup_status = "ready";
        db.writeups[bk.id] = writeupFrom(notes);
      }
    } else if (seg[2] === "notes") {
      if (bk.status !== "completed") err("invalid_state", "Notes can only be added to a completed call.");
      if (!notes) err("validation_error", "Write some notes first.");
      bk.writeup_status = "ready";
      db.writeups[bk.id] = writeupFrom(notes);
    }
    save(db);
    return result(stripToken(bk, false));
  }

  if (seg[0] === "admin") {
    if (headers["X-Admin-Password"] !== MOCK_ADMIN_PASSWORD) err("unauthorized", "Wrong password. Check it and try again.");
    return result(seedAdmin(db));
  }

  return err("not_found", "Not found.");
}
