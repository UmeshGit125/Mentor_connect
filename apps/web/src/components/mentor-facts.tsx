import type { PublicMentor } from "@/lib/types";
import { FIELD_LABELS } from "@/components/evidence";

function Fact({ field, children }: { field: string; children: React.ReactNode | null }) {
  const missing = children === null;
  return (
    <div data-testid="fact" data-field={field} className={`grid grid-cols-[8.5rem_1fr] gap-x-3 rounded-control px-3 py-2.5 ${missing ? "border border-dashed border-[#c6cfce]" : "border border-line bg-white"}`}>
      <dt className="text-sm text-muted">{FIELD_LABELS[field]}</dt>
      <dd className={missing ? "text-sm text-muted" : "font-medium"}>{missing ? "Not stated" : children}</dd>
    </div>
  );
}

const list = (a: string[]) => (a.length ? a.join(", ") : null);

export function MentorFacts({ mentor: m }: { mentor: PublicMentor }) {
  const tools = Object.entries(m.tools).filter(([, v]) => v).map(([k]) => k.replace("_", " "));
  return (
    <dl className="grid gap-2 md:grid-cols-2">
      <Fact field="domain">{m.domain}</Fact>
      <Fact field="company">{m.company}</Fact>
      <Fact field="city">{m.city}</Fact>
      <Fact field="sector">{m.sector}</Fact>
      <Fact field="sectors">{list(m.sectors)}</Fact>
      <Fact field="roles">{list(m.roles)}</Fact>
      <Fact field="seniority">{m.seniority}</Fact>
      <Fact field="built_ai">{m.built_ai === null ? null : m.built_ai ? "Yes" : "No"}</Fact>
      <Fact field="ai_tools">{list(m.ai_tools)}</Fact>
      <Fact field="tools">{list(tools)}</Fact>
      <Fact field="quality">{m.quality}</Fact>
      <Fact field="activities">{m.activities === null ? null : <span className="tnum">{m.activities}</span>}</Fact>
    </dl>
  );
}
