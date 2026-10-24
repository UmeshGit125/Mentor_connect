import type {
  AdminSummary,
  Booking,
  ChatReply,
  ChatTranscript,
  ErrorCode,
  MentorFilters,
  PublicMentor,
  Slot,
  Student,
  Writeup,
} from "@/lib/types";

const BASE = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");
export const USE_MOCKS = process.env.NEXT_PUBLIC_USE_MOCKS === "1";

/** Typed error built from the contract error shape. `network` means no response. */
export class ApiError extends Error {
  constructor(
    public code: ErrorCode | "network",
    message: string,
    public status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export function errorMessage(e: unknown): string {
  if (e instanceof ApiError) return e.message;
  return "Something went wrong. Try again.";
}

type Method = "GET" | "POST";
export type Headers = Record<string, string>;

async function request<T>(method: Method, path: string, body?: unknown, headers: Headers = {}): Promise<T> {
  if (USE_MOCKS) {
    // Dynamic import keeps fixtures out of the production bundle when mocks are off.
    const { mockRequest } = await import("@/mocks/handlers");
    return mockRequest<T>(method, path, body, headers);
  }
  let res: Response;
  try {
    res = await fetch(`${BASE}/api${path}`, {
      method,
      headers: { ...(body !== undefined ? { "Content-Type": "application/json" } : {}), ...headers },
      body: body !== undefined ? JSON.stringify(body) : undefined,
      cache: "no-store",
    });
  } catch {
    throw new ApiError("network", "Can't reach the server. Check your connection and try again.", 0);
  }
  if (!res.ok) {
    let code: ErrorCode = "validation_error";
    let message = "The request failed. Try again.";
    try {
      const data = await res.json();
      if (data?.error) {
        code = data.error.code;
        message = data.error.message;
      }
    } catch {
      // Non-JSON error body: keep the generic message.
    }
    throw new ApiError(code, message, res.status);
  }
  return (await res.json()) as T;
}

function student(id: string | null): Headers {
  return id ? { "X-Student-Id": id } : {};
}

function qs(f: MentorFilters): string {
  const p = new URLSearchParams();
  for (const [k, v] of Object.entries(f)) if (v) p.set(k, v);
  const s = p.toString();
  return s ? `?${s}` : "";
}

export const api = {
  listMentors: (f: MentorFilters = {}) => request<PublicMentor[]>("GET", `/mentors${qs(f)}`),
  getMentor: (id: string) => request<PublicMentor>("GET", `/mentors/${encodeURIComponent(id)}`),
  getSlots: (id: string) => request<Slot[]>("GET", `/mentors/${encodeURIComponent(id)}/slots`),
  createStudent: (name: string, email: string) => request<Student>("POST", "/students", { name, email }),
  chat: (sid: string | null, message: string, studentId: string | null) =>
    request<ChatReply>("POST", "/chat", { ...(sid ? { session_id: sid } : {}), message }, student(studentId)),
  getChat: (sid: string) => request<ChatTranscript>("GET", `/chat/${encodeURIComponent(sid)}`),
  book: (mentorId: string, slotId: string, sessionId: string, studentId: string | null) =>
    request<Booking>(
      "POST",
      "/bookings",
      { mentor_id: mentorId, slot_id: slotId, session_id: sessionId },
      student(studentId),
    ),
  listBookings: (studentId: string | null) => request<Booking[]>("GET", "/bookings", undefined, student(studentId)),
  getBooking: (id: string, studentId: string | null) =>
    request<Booking>("GET", `/bookings/${encodeURIComponent(id)}`, undefined, student(studentId)),
  cancel: (id: string, studentId: string | null) =>
    request<Booking>("POST", `/bookings/${encodeURIComponent(id)}/cancel`, undefined, student(studentId)),
  getWriteup: (id: string, studentId: string | null) =>
    request<Writeup>("GET", `/bookings/${encodeURIComponent(id)}/writeup`, undefined, student(studentId)),
  getMentorPage: (token: string) =>
    request<{ booking: Booking; student_name: string }>("GET", `/m/${encodeURIComponent(token)}`),
  close: (token: string, outcome: "completed" | "no_show", notes?: string) =>
    request<Booking>("POST", `/m/${encodeURIComponent(token)}/close`, {
      outcome,
      ...(notes ? { notes } : {}),
    }),
  addNotes: (token: string, notes: string) =>
    request<Booking>("POST", `/m/${encodeURIComponent(token)}/notes`, { notes }),
  sendContact: (name: string, email: string, message: string) =>
    request<{ id: string; status: "received" }>("POST", "/contact", { name, email, message }),
  adminSummary: (password: string) =>
    request<AdminSummary>("GET", "/admin/summary", undefined, { "X-Admin-Password": password }),
};
