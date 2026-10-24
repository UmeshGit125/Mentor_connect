import type { PublicMentor, Reason } from "@/lib/types";

export const FIELD_LABELS: Record<string, string> = {
  domain: "Domain",
  company: "Company",
  city: "City",
  sector: "Sector",
  sectors: "Sectors of expertise",
  roles: "Roles of expertise",
  seniority: "Seniority",
  built_ai: "Has built AI",
  ai_tools: "AI tools",
  tools: "Tools",
  quality: "Quality rating",
  activities: "Sessions done",
};

// Fields we always account for on a card: shown as evidence or as "Not stated".
const ALWAYS_SHOWN = ["sector", "company", "city", "seniority"] as const;

/** A value confirmed from the mentor sheet. The tick is decorative; the text carries the meaning. */
export function EvidenceRow({ reason }: { reason: Reason }) {
  return (
    <li data-testid="reason-row" data-field={reason.field} className="grid grid-cols-[7.5rem_1fr] gap-x-3 rounded-control bg-mint px-3 py-2.5">
      <span className="text-sm text-muted">{FIELD_LABELS[reason.field] ?? reason.field}</span>
      <span>
        <span data-testid="reason-value" className="flex items-start gap-1.5 text-[0.95rem] font-semibold tnum">
          <svg aria-hidden="true" width="16" height="16" viewBox="0 0 16 16" className="mt-[5px] shrink-0 text-brand-dark">
            <path d="M3 8.5l3.2 3L13 4.5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          {reason.value}
        </span>
        <span className="mt-0.5 block text-sm text-muted">{reason.text}</span>
      </span>
    </li>
  );
}

/** The sheet leaves this blank. Say so, never hide it, never guess. */
export function MissingRow({ field }: { field: string }) {
  return (
    <li data-testid="reason-missing" data-field={field} className="grid grid-cols-[7.5rem_1fr] gap-x-3 rounded-control border border-dashed border-[#c6cfce] px-3 py-2.5">
      <span className="text-sm text-muted">{FIELD_LABELS[field] ?? field}</span>
      <span className="text-sm text-muted">Not stated</span>
    </li>
  );
}

export function EvidenceList({ mentor, reasons }: { mentor: PublicMentor; reasons: Reason[] }) {
  const cited = new Set(reasons.map((r) => r.field));
  const missing = ALWAYS_SHOWN.filter((f) => mentor[f] === null && !cited.has(f));
  return (
    <ul className="space-y-2" aria-label={`Why ${mentor.name} fits`}>
      {reasons.map((r) => (
        <EvidenceRow key={r.field} reason={r} />
      ))}
      {missing.map((f) => (
        <MissingRow key={f} field={f} />
      ))}
    </ul>
  );
}
