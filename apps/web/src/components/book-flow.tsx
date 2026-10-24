"use client";
import Link from "next/link";
import { useState } from "react";
import { MentorLink } from "@/components/mentor-link";
import { SignIn } from "@/components/sign-in";
import { SlotPicker } from "@/components/slot-picker";
import { StatusPill } from "@/components/status-pill";
import { ErrorState, Loading } from "@/components/states";
import { api, ApiError, errorMessage } from "@/lib/api";
import { lastChatSession } from "@/lib/chat-session";
import { fullLabel } from "@/lib/format";
import { getStudentId, useStudent } from "@/lib/student";
import { useLoad } from "@/lib/use-load";
import type { Booking } from "@/lib/types";

export function BookFlow({ mentorId, initialSlot }: { mentorId: string; initialSlot?: string }) {
  const { student, ready } = useStudent();
  // Mentor and slots load together, so there is no waterfall.
  const { data, error, loading, reload } = useLoad(
    () => Promise.all([api.getMentor(mentorId), api.getSlots(mentorId)]),
    ready && student ? mentorId : null,
  );
  const [slotId, setSlotId] = useState<string | null>(initialSlot ?? null);
  const [busy, setBusy] = useState(false);
  const [problem, setProblem] = useState<{ message: string; cap: boolean } | null>(null);
  const [booking, setBooking] = useState<Booking | null>(null);

  if (!ready) return <Loading rows={2} />;
  if (!student) return <SignIn lead="Sign in so we can attach this booking to you." />;
  if (loading) return <Loading rows={3} label="Loading times" />;
  if (error || !data) return <ErrorState title="Booking page did not load" message={error ?? "Try again."} onRetry={reload} />;
  const [mentor, slots] = data;

  if (booking) {
    return (
      <section data-testid="booking-confirmation" aria-labelledby="done-h" className="panel space-y-4 border-brand p-6 md:p-8">
        <div className="flex flex-wrap items-center gap-3">
          <h1 id="done-h" className="h-page">Call booked</h1>
          <StatusPill status={booking.status} />
        </div>
        <p data-testid="booking-when" className="text-lg tnum">{fullLabel(booking.slot.start)} with {booking.mentor.name}</p>
        <p className="measure text-muted">The call happens outside this app. Your mentor gets a short brief from your chat. After the call you will see a write-up under My sessions.</p>
        {booking.mentor_token ? <MentorLink token={booking.mentor_token} /> : null}
        <div className="flex flex-wrap gap-2">
          <Link href={`/sessions/${booking.id}`} data-testid="view-booking" className="btn btn-primary">View booking</Link>
          <Link href="/sessions" className="btn btn-quiet">All sessions</Link>
        </div>
      </section>
    );
  }

  async function confirm() {
    if (!slotId) return;
    setBusy(true);
    setProblem(null);
    try {
      setBooking(await api.book(mentorId, slotId, lastChatSession(), getStudentId()));
    } catch (e) {
      const cap = e instanceof ApiError && (e.code === "booking_cap_reached" || e.code === "mentor_cap_reached");
      setProblem({ message: errorMessage(e), cap });
      if (e instanceof ApiError && e.code === "slot_taken") {
        // Drop the stale choice and refresh times so the next pick is real.
        setSlotId(null);
        void reload();
      }
    } finally {
      setBusy(false);
    }
  }

  const chosen = slots.find((s) => s.id === slotId);
  return (
    <div className="space-y-8">
      <div>
        <h1 className="h-page">Book {mentor.name}</h1>
        <p className="mt-1 text-muted">{mentor.domain}{mentor.company ? ` at ${mentor.company}` : ""}</p>
      </div>
      <SlotPicker slots={slots} selected={slotId} onSelect={setSlotId} disabled={busy} />
      {problem ? (
        <div role="alert" data-testid="booking-error" className="rounded-card border border-danger/40 bg-danger-wash p-4">
          <p>{problem.message}</p>
          {problem.cap ? <Link href="/sessions" className="mt-2 inline-block font-semibold text-signal underline underline-offset-4">Go to my sessions</Link> : null}
        </div>
      ) : null}
      <div className="panel flex flex-wrap items-center justify-between gap-3 p-4">
        <p data-testid="selected-slot" className="tnum">{chosen ? fullLabel(chosen.start) : "Pick a time to continue"}</p>
        <button type="button" data-testid="confirm-booking" disabled={!chosen || busy} onClick={confirm} className="btn btn-primary">
          {busy ? "Booking…" : "Confirm booking"}
        </button>
      </div>
    </div>
  );
}
