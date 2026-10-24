import type { Metadata } from "next";
import Link from "next/link";
import { MentorCard } from "@/components/mentor-card";
import { EmptyState, ErrorState } from "@/components/states";
import { api, errorMessage } from "@/lib/api";
import type { PublicMentor } from "@/lib/types";

export const metadata: Metadata = { title: "Browse mentors" };
export const dynamic = "force-dynamic";

type Params = { q?: string; domain?: string; sector?: string; city?: string };

export default async function MentorsPage({ searchParams }: { searchParams: Promise<Params> }) {
  const f = await searchParams;
  // Both requests start together: the filtered list and the full list that feeds the filter options.
  let shown: PublicMentor[];
  let all: PublicMentor[];
  try {
    // Both requests start together: the filtered list and the full list that feeds the filter options.
    [shown, all] = await Promise.all([api.listMentors(f), api.listMentors()]);
  } catch (e) {
    return (
      <div className="page space-y-4">
        <h1 className="h-page">Mentors</h1>
        <ErrorState title="Mentors did not load" message={`${errorMessage(e)} Refresh the page to try again.`} />
      </div>
    );
  }
  const options = (pick: (m: PublicMentor) => string | null) =>
    [...new Set(all.map(pick).filter((v): v is string => !!v))].sort();
  const domains = options((m) => m.domain);
  const sectors = options((m) => m.sector);
  const cities = options((m) => m.city);
  const active = Object.values(f).some(Boolean);

  return (
    <div className="page">
      <h1 className="h-page">Mentors</h1>
      <p className="mt-1 text-sm text-muted">
        All {all.length} mentors. Not sure who fits? <Link href="/" className="font-semibold text-signal underline underline-offset-4">Describe your problem instead</Link>.
      </p>
      <form method="get" role="search" data-testid="mentor-filters" className="mt-8 grid gap-3 sm:grid-cols-2 lg:grid-cols-[1.3fr_1fr_1fr_1fr_auto_auto]">
        <div>
          <label htmlFor="f-q" className="sr-only">Search by name, company or role</label>
          <input id="f-q" name="q" type="search" defaultValue={f.q} placeholder="Search" autoComplete="off" className="field" data-testid="filter-q" />
        </div>
        {([["domain", "Domain", "All domains", domains], ["sector", "Sector", "All sectors", sectors], ["city", "City", "All cities", cities]] as const).map(([name, label, any, opts]) => (
          <div key={name}>
            <label htmlFor={`f-${name}`} className="sr-only">{label}</label>
            <select id={`f-${name}`} name={name} defaultValue={f[name] ?? ""} className="field" data-testid={`filter-${name}`}>
              <option value="">{any}</option>
              {opts.map((o) => <option key={o} value={o}>{o}</option>)}
            </select>
          </div>
        ))}
        <button type="submit" className="btn btn-outline-brand lg:min-w-[130px]" data-testid="filter-apply">
          <svg aria-hidden="true" width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"><circle cx="7" cy="7" r="5" /><path d="M11 11l3.5 3.5" /></svg>
          Search
        </button>
        {active ? <Link href="/mentors" className="btn btn-quiet">Clear</Link> : <span className="hidden lg:block" />}
      </form>
      <p className="tnum mt-6 text-sm text-muted" aria-live="polite" data-testid="mentor-count">{shown.length} shown</p>
      {shown.length ? (
        <ul className="mt-4 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {shown.map((m) => <MentorCard key={m.id} mentor={m} />)}
        </ul>
      ) : (
        <div className="mt-4">
          <EmptyState title="No mentors match those filters" body="Remove a filter or search for something broader, like a domain instead of a company." href="/mentors" cta="Clear filters" />
        </div>
      )}
    </div>
  );
}
