// Types copied from docs/CONTRACT.md (v1.3). Keep in sync with the contract.

export type ErrorCode =
  | "validation_error"
  | "not_found"
  | "unauthorized"
  | "slot_taken"
  | "booking_cap_reached"
  | "mentor_cap_reached"
  | "invalid_state"
  | "ai_unavailable"
  | "rate_limited";

export type PublicMentor = {
  id: string;
  name: string;
  city: string | null;
  domain: string;
  company: string | null;
  sector: string | null;
  sectors: string[];
  roles: string[];
  seniority: "Mid-career" | "Senior" | null;
  built_ai: boolean | null;
  ai_tools: string[];
  tools: {
    tableau: boolean | null;
    hubspot: boolean | null;
    google_analytics: boolean | null;
    jira: boolean | null;
    excel: boolean | null;
    mixpanel: boolean | null;
  };
  quality: "Excellent" | "Good" | null;
  activities: number | null;
};

export type Reason = { field: string; value: string; text: string };
export type Match = { mentor: PublicMentor; reasons: Reason[] };
export type Need = {
  summary: string;
  domains: string[];
  sectors: string[];
  tools: string[];
  wants_ai: boolean;
};

export type ChatKind = "clarify" | "matches" | "no_match" | "redirect";
export type ChatReply = {
  session_id: string;
  kind: ChatKind;
  message: string;
  matches: Match[];
  need: Need | null;
};

export type Slot = {
  id: string;
  mentor_id: string;
  start: string;
  end: string;
  status: "open" | "booked";
};

export type BookingStatus = "confirmed" | "completed" | "no_show" | "cancelled";
export type WriteupStatus = "none" | "notes_received" | "ready";

export type Booking = {
  id: string;
  student_id: string;
  mentor: PublicMentor;
  slot: Slot;
  status: BookingStatus;
  brief: string;
  created_at: string;
  writeup_status: WriteupStatus;
  /** Demo only: private mentor link token, set only in the owning student's views. */
  mentor_token: string | null;
};

export type Writeup = {
  status: WriteupStatus;
  discussed: string[];
  work_on: string[];
  next_steps: string[];
};

export type Student = { id: string; name: string; email: string };

export type ChatTranscript = {
  messages: { role: "student" | "assistant"; text: string }[];
  last: ChatReply | null;
};

export type AdminSummary = {
  funnel: {
    chats_started: number;
    matched: number;
    booked: number;
    completed: number;
    writeups_ready: number;
    rebooked: number;
  };
  bookings_by_status: Record<BookingStatus, number>;
  stuck: Booking[];
  unmatched: { id: string; created_at: string; summary: string }[];
  mentor_load: { mentor_id: string; name: string; active: number; completed: number }[];
};

export type MentorFilters = { q?: string; domain?: string; sector?: string; city?: string };
