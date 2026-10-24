import Link from "next/link";
import { avatarText } from "@/lib/format";
import type { PublicMentor } from "@/lib/types";

function Stat({ label, value }: { label: string; value: string | null }) {
  return (
    <div className="min-w-0 px-3 first:pl-0 last:pr-0 [&:not(:first-child)]:border-l [&:not(:first-child)]:border-line">
      <dt className="text-[0.8rem] text-muted">{label}</dt>
      <dd className={`mt-0.5 text-sm ${value ? "font-medium" : "text-muted"}`}>{value ?? "Not stated"}</dd>
    </div>
  );
}

/** Browse-grid card: initials block (the sheet has no photos), name, domain, two real fields. No ratings or badges. */
export function MentorCard({ mentor }: { mentor: PublicMentor }) {
  return (
    <li data-testid="mentor-card" data-mentor-id={mentor.id}>
      <Link href={`/mentors/${mentor.id}`} className="panel lift flex h-full flex-col p-2.5">
        <div aria-hidden="true" className="grid aspect-[1/0.92] place-items-center rounded-[4px] bg-mint text-[clamp(2.5rem,5vw,3.75rem)] font-semibold tracking-wide text-signal">
          {avatarText(mentor.name)}
        </div>
        <div className="flex flex-1 flex-col px-2.5 pb-3 pt-4">
          <h3 className="block text-[1.1rem] font-semibold leading-tight">{mentor.name}</h3>
          <div className="mt-2 flex items-start gap-2 text-sm text-muted">
            <svg aria-hidden="true" width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.4" className="mt-0.5 shrink-0">
              <rect x="1.7" y="4.5" width="12.6" height="8.8" rx="1.4" /><path d="M5.5 4.5V3.2c0-.5.4-.9.9-.9h3.2c.5 0 .9.4.9.9v1.3M1.7 8.3h12.6" />
            </svg>
            {mentor.domain}
          </div>
          <dl className="mt-auto grid grid-cols-2 pt-4">
            <Stat label="Company" value={mentor.company} />
            <Stat label="City" value={mentor.city} />
          </dl>
        </div>
      </Link>
    </li>
  );
}
