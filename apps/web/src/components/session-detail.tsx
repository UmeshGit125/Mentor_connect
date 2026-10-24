"use client";
import Link from "next/link";
import { useState } from "react";
import { MentorLink } from "@/components/mentor-link";
import { SignIn } from "@/components/sign-in";
import { StatusPill, WriteupPill } from "@/components/status-pill";
import { ErrorState, Loading } from "@/components/states";
import { api, errorMessage } from "@/lib/api";
import { fullLabel } from "@/lib/format";
import { getStudentId, useStudent } from "@/lib/student";
import { useLoad } from "@/lib/use-load";
import type { Booking, Writeup } from "@/lib/types";

// Plain-language reason for each state in which there is no write-up.
function noWriteupReason(b: Booking, w: Writeup | null): string {
  if (b.status === "confirmed") return "The call has not happened yet. Your mentor adds notes after it.";
  if (b.status === "cancelled") return "This call was cancelled, so there is nothing to write up.";
  if (b.status === "no_show") return "The call was marked as a no-show, so there are no notes to write up.";
  if (w?.status === "notes_received") return "Your mentor's notes are in. The write-up is being prepared, so check back shortly.";
  return "Your mentor closed the call without notes. Write-ups are only made from real notes.";
}

function List({ title, items, testid }: { title: string; items: string[]; testid: string }) {
  return (
    <section data-testid={testid} aria-labelledby={`${testid}-h`}>
      <h3 id={`${testid}-h`} className="text-lg font-semibold">{title}</h3>
      <ul className="mt-2 list-disc space-y-1.5 pl-5 measure">
        {items.map((t, i) => <li key={i}>{t}</li>)}
      </ul>
    </section>
  );
}

export function SessionDetail({ id }: { id: string }) {
  const { student, ready } = useStudent();
  const key = ready && student ? id : null;
  const booking = useLoad(() => api.getBooking(id, getStudentId()), key);
  // The write-up request does not depend on the booking response, so both start together.
  const writeup = useLoad(() => api.getWriteup(id, getStudentId()), key);
  const [cancelling, setCancelling] = useState(false);
  const [confirmCancel, setConfirmCancel] = useState(false);
  const [cancelError, setCancelError] = useState<string | null>(null);

  if (!ready) return <Loading rows={2} />;
  if (!student) return <SignIn lead="Sign in to see this booking." />;
  if (booking.loading) return <Loading label="Loading booking" />;
  if (booking.error || !booking.data) return <ErrorState title="Booking did not load" message={booking.error ?? "Try again."} onRetry={booking.reload} />;
  const b = booking.data;
  const w = writeup.data;

  async function cancel() {
    setCancelling(true);
    setCancelError(null);
    try {
      booking.setData(await api.cancel(id, getStudentId()));
    } catch (e) {
      setCancelError(errorMessage(e));
    } finally {
      setCancelling(false);
    }
  }

  return (
    <div className="space-y-8">
      <header className="space-y-2">
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="h-page">{b.mentor.name}</h1>
          <StatusPill status={b.status} />
        </div>
        <p className="tnum text-lg text-muted" data-testid="booking-when">{fullLabel(b.slot.start)}</p>
        <p className="text-muted">{b.mentor.domain}{b.mentor.company ? ` at ${b.mentor.company}` : ""}</p>
      </header>

      <section aria-labelledby="brief-h">
        <h2 id="brief-h" className="text-xl">What your mentor sees</h2>
        <p data-testid="booking-brief" className="mt-3 measure rounded-card border border-line bg-wash p-4">{b.brief}</p>
      </section>

      <section aria-labelledby="writeup-h" className="space-y-4">
        <div className="flex flex-wrap items-center gap-3">
          <h2 id="writeup-h" className="text-xl">Write-up</h2>
          <WriteupPill status={w?.status ?? b.writeup_status} />
        </div>
        {writeup.loading ? (
          <Loading rows={1} label="Loading write-up" />
        ) : writeup.error ? (
          <ErrorState title="Write-up did not load" message={writeup.error} onRetry={writeup.reload} />
        ) : w?.status === "ready" ? (
          <div data-testid="writeup" className="panel space-y-6 p-6">
            <List title="What you discussed" items={w.discussed} testid="writeup-discussed" />
            <List title="What to work on" items={w.work_on} testid="writeup-work-on" />
            <List title="Next steps" items={w.next_steps} testid="writeup-next-steps" />
          </div>
        ) : (
          <div data-testid="writeup-none" className="rounded-card border border-dashed border-[#c6cfce] bg-wash p-5">
            <p className="font-semibold">No write-up yet</p>
            <p className="mt-1 measure text-muted">{noWriteupReason(b, w)}</p>
          </div>
        )}
      </section>

      {b.status === "confirmed" && b.mentor_token ? <MentorLink token={b.mentor_token} /> : null}

      {b.status === "confirmed" ? (
        <div>
          {cancelError ? <p role="alert" className="mb-2 font-medium text-danger">{cancelError}</p> : null}
          {confirmCancel ? (
            <div role="group" aria-label="Confirm cancellation" className="flex flex-wrap items-center gap-2">
              <span>Cancel this call and free the slot?</span>
              <button type="button" data-testid="cancel-confirm" disabled={cancelling} onClick={cancel} className="btn btn-quiet">
                {cancelling ? "Cancelling…" : "Yes, cancel call"}
              </button>
              <button type="button" onClick={() => setConfirmCancel(false)} className="btn btn-quiet">Keep call</button>
            </div>
          ) : (
            <button type="button" data-testid="cancel-booking" onClick={() => setConfirmCancel(true)} className="btn btn-quiet">Cancel this call</button>
          )}
        </div>
      ) : null}
      <Link href="/sessions" className="inline-block font-semibold text-signal underline underline-offset-4">Back to my sessions</Link>
    </div>
  );
}
