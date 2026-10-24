import type { BookingStatus, WriteupStatus } from "@/lib/types";

const BOOKING: Record<BookingStatus, { label: string; cls: string; mark: string }> = {
  confirmed: { label: "Confirmed", cls: "border-brand/40 bg-mint text-signal", mark: "●" },
  completed: { label: "Completed", cls: "border-transparent bg-brand text-white", mark: "✓" },
  no_show: { label: "No-show", cls: "border-danger/40 bg-danger-wash text-danger", mark: "!" },
  cancelled: { label: "Cancelled", cls: "border-line bg-wash text-muted", mark: "×" },
};

// Every pill carries a plain word and a glyph, so colour is never the only signal.
export function StatusPill({ status }: { status: BookingStatus }) {
  const s = BOOKING[status];
  return (
    <span data-testid="booking-status" data-status={status} className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[0.8rem] font-semibold ${s.cls}`}>
      <span aria-hidden="true">{s.mark}</span>
      {s.label}
    </span>
  );
}

const WRITEUP: Record<WriteupStatus, string> = {
  none: "No write-up yet",
  notes_received: "Write-up in progress",
  ready: "Write-up ready",
};

export function WriteupPill({ status }: { status: WriteupStatus }) {
  return (
    <span data-testid="writeup-status" data-status={status} className="inline-flex items-center rounded-full border border-line bg-wash px-2.5 py-0.5 text-[0.8rem] font-medium text-muted">
      {WRITEUP[status]}
    </span>
  );
}
