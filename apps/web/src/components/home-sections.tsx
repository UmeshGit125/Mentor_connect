import Link from "next/link";
import { ICONS, CATEGORY_ICONS, type IconName } from "@/components/icons";
import { MentorCard } from "@/components/mentor-card";
import type { PublicMentor } from "@/lib/types";

function Heading({ eyebrow, title, className = "text-center" }: { eyebrow: string; title: string; className?: string }) {
  return (
    <div className={className}>
      <span className="eyebrow">{eyebrow}</span>
      <h2 className="h-section mx-auto mt-5 max-w-3xl">{title}</h2>
    </div>
  );
}

function IconCircle({ name, size = "sm" }: { name: IconName; size?: "sm" | "lg" }) {
  return (
    <span aria-hidden="true" className={`grid shrink-0 place-items-center rounded-full border border-line bg-white text-brand ${size === "lg" ? "size-[104px] [&_svg]:size-11" : "size-[72px]"}`}>
      {ICONS[name]}
    </span>
  );
}

const STEPS: { icon: IconName; title: string; body: string }[] = [
  { icon: "pen", title: "Describe your problem", body: "Write it the way you would tell a friend. No forms, no keywords." },
  { icon: "search", title: "See why each mentor fits", body: "Every pick shows the real profile values behind it, and says so when something is not stated." },
  { icon: "calendar", title: "Book a call and get a write-up", body: "Pick a 30-minute slot. After the call you get a short write-up with next steps." },
];

const FEATURES: { icon: IconName; title: string; body: string }[] = [
  { icon: "badge", title: "Evidence-based matching", body: "Up to three mentors per problem, each with the exact profile fields that make it a fit." },
  { icon: "search", title: "Search and filter", body: "Browse all mentors and filter by domain, sector and city, or search by name, company or role." },
  { icon: "calendar", title: "Slot booking", body: "See open times for the next seven days and book one. A slot can only be booked once." },
  { icon: "note", title: "Call write-ups", body: "After the call your mentor adds notes and you get what was discussed, what to work on and next steps." },
  { icon: "shield", title: "Privacy first", body: "Mentor email, phone and LinkedIn are never shown. The call itself happens outside the app." },
  { icon: "bars", title: "Funnel for the Mesa team", body: "An admin page shows chats, matches, bookings, completed calls and anything stuck." },
];

export function WorkflowSection() {
  return (
    <section aria-labelledby="workflow-h" className="py-20 md:py-24">
      <div className="wrap">
        <div id="workflow-h"><Heading eyebrow="Workflow" title="From a stuck moment to a booked call in three steps" /></div>
        <ol className="mt-14 grid gap-6 md:grid-cols-3">
          {STEPS.map((s) => (
            <li key={s.title} className="lift rounded-card bg-white px-8 py-10 text-center">
              <div className="flex justify-center"><IconCircle name={s.icon} size="lg" /></div>
              <h3 className="mt-7 text-[1.2rem]">{s.title}</h3>
              <p className="mx-auto mt-3 max-w-xs text-[0.95rem] leading-7 text-muted">{s.body}</p>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}

export function CategoriesSection({ mentors }: { mentors: PublicMentor[] }) {
  const counts = new Map<string, number>();
  for (const m of mentors) counts.set(m.domain, (counts.get(m.domain) ?? 0) + 1);
  const cats = [...counts.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
  if (!cats.length) return null;
  return (
    <section aria-labelledby="cats-h" className="bg-wash py-20 md:py-24">
      <div className="wrap">
        <div id="cats-h"><Heading eyebrow="Categories" title="Browse Mentors by Categories" /></div>
        <ul className="mt-14 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {cats.map(([domain, n], i) => (
            <li key={domain}>
              <Link href={`/mentors?domain=${encodeURIComponent(domain)}`} className="panel lift flex h-full flex-col items-center px-4 py-8 text-center !shadow-none">
                <IconCircle name={CATEGORY_ICONS[i % CATEGORY_ICONS.length]} />
                <span className="mt-5 text-[1.15rem] font-semibold leading-snug">{domain}</span>
                <span className="mt-1.5 text-sm text-muted">{n} {n === 1 ? "Mentor" : "Mentors"}</span>
              </Link>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}

export function FeaturesSection() {
  return (
    <section aria-labelledby="feat-h" className="py-20 md:py-24">
      <div className="wrap">
        <div id="feat-h"><Heading eyebrow="Features" title="Everything you need to go from stuck to booked." /></div>
        <ul className="mt-14 grid overflow-hidden rounded-card border-l border-t border-line md:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((f) => (
            <li key={f.title} className="group border-b border-r border-line bg-white p-8 transition-colors hover:bg-brand hover:text-white">
              <span aria-hidden="true" className="grid size-[68px] place-items-center rounded-full border border-line bg-white text-brand">{ICONS[f.icon]}</span>
              <h3 className="mt-6 text-[1.2rem] font-semibold">{f.title}</h3>
              <p className="mt-3 text-[0.95rem] leading-7 text-muted transition-colors group-hover:text-white">{f.body}</p>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}

export function DiscoverSection({ mentors }: { mentors: PublicMentor[] }) {
  // The four most active mentors when the sheet has activity counts, otherwise the first four.
  const withActivity = mentors.filter((m) => m.activities !== null);
  const picks = (withActivity.length >= 4
    ? [...withActivity].sort((a, b) => (b.activities ?? 0) - (a.activities ?? 0))
    : mentors
  ).slice(0, 4);
  if (!picks.length) return null;
  return (
    <section aria-labelledby="disc-h" className="pb-24 pt-4">
      <div className="wrap">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <h2 id="disc-h" className="h-section">Discover our mentors</h2>
          <Link href="/mentors" className="font-semibold text-signal underline-offset-4 hover:underline">View all mentors →</Link>
        </div>
        <ul className="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {picks.map((m) => <MentorCard key={m.id} mentor={m} />)}
        </ul>
      </div>
    </section>
  );
}
