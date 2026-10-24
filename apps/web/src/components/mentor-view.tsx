"use client";
import { useState } from "react";
import { StatusPill, WriteupPill } from "@/components/status-pill";
import { ErrorState, Loading } from "@/components/states";
import { api, errorMessage } from "@/lib/api";
import { fullLabel } from "@/lib/format";
import { useLoad } from "@/lib/use-load";
import type { Booking } from "@/lib/types";

export function MentorView({ token }: { token: string }) {
  const { data, setData, error, loading, reload } = useLoad(() => api.getMentorPage(token), token);
  const [notes, setNotes] = useState("");
  const [busy, setBusy] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);

  if (loading) return <Loading label="Loading call details" />;
  if (error || !data) return <ErrorState title="This link did not open" message={error ?? "Check the link and try again."} onRetry={reload} />;
  const b = data.booking;

  async function act(fn: () => Promise<Booking>) {
    setBusy(true);
    setProblem(null);
    try {
      const next = await fn();
      setData({ booking: next, student_name: data!.student_name });
      setNotes("");
    } catch (e) {
      setProblem(errorMessage(e));
    } finally {
      setBusy(false);
    }
  }

  const open = b.status === "confirmed";
  const canAddNotes = b.status === "completed" && b.writeup_status === "none";

  return (
    <div className="space-y-8">
      <header className="space-y-2">
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="h-page">Call with {data.student_name}</h1>
          <StatusPill status={b.status} />
        </div>
        <p className="tnum text-lg text-muted" data-testid="mentor-call-time">{fullLabel(b.slot.start)}</p>
      </header>

      <section aria-labelledby="brief-h">
        <h2 id="brief-h" className="text-xl">Brief</h2>
        <p data-testid="mentor-brief" className="mt-3 measure rounded-card border border-line bg-wash p-4">{b.brief}</p>
      </section>

      {open || canAddNotes ? (
        <section aria-labelledby="notes-h" className="space-y-3">
          <h2 id="notes-h" className="text-xl">{open ? "After the call" : "Add notes"}</h2>
          <div className="grid gap-4 md:grid-cols-[1fr_16rem]">
            <div>
              <label htmlFor="notes" className="mb-1 block text-sm font-medium">Notes</label>
              <textarea id="notes" name="notes" autoComplete="off" data-testid="notes-box" rows={7} maxLength={8000} value={notes} onChange={(e) => setNotes(e.target.value)} className="field" placeholder="What you covered, what the student should work on, next steps…" />
              <p className="mt-1 text-sm text-muted tnum">{notes.length} of 8000. The student&apos;s write-up is made only from these notes.</p>
            </div>
            <div className="self-start rounded-card border border-dashed border-[#c6cfce] bg-wash p-4">
              <label className="flex items-start gap-2 text-muted">
                <input type="checkbox" disabled data-testid="audio-upload" className="mt-1" />
                <span>Upload audio, coming soon</span>
              </label>
            </div>
          </div>
          {problem ? <p role="alert" data-testid="mentor-error" className="rounded-card border border-danger/40 bg-danger-wash p-3 font-medium text-danger">{problem}</p> : null}
          <div className="flex flex-wrap gap-2">
            {open ? (
              <>
                <button type="button" data-testid="close-completed" disabled={busy} onClick={() => act(() => api.close(token, "completed", notes.trim() || undefined))} className="btn btn-primary">Close as completed</button>
                <button type="button" data-testid="close-no-show" disabled={busy} onClick={() => act(() => api.close(token, "no_show"))} className="btn btn-quiet">Close as no-show</button>
              </>
            ) : (
              <button type="button" data-testid="save-notes" disabled={busy || !notes.trim()} onClick={() => act(() => api.addNotes(token, notes.trim()))} className="btn btn-primary">Save notes</button>
            )}
          </div>
        </section>
      ) : (
        <section data-testid="mentor-closed" className="panel p-6">
          <p className="font-medium">{b.status === "completed" ? "Call closed as completed" : b.status === "no_show" ? "Call closed as no-show" : "This call was cancelled"}</p>
          <div className="mt-2"><WriteupPill status={b.writeup_status} /></div>
          <p className="mt-2 text-muted">{b.status === "completed" ? "Thank you. The student can see their write-up now." : "Nothing more to do on this link."}</p>
        </section>
      )}
    </div>
  );
}
