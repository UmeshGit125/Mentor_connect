import Link from "next/link";
import { EvidenceList } from "@/components/evidence";
import { avatarText } from "@/lib/format";
import type { Match } from "@/lib/types";

/** The signature element: a mentor plus the exact sheet values that justify the match. */
export function RecommendationCard({ match, index = 0 }: { match: Match; index?: number }) {
  const { mentor, reasons } = match;
  return (
    <article
      data-testid="mentor-card"
      data-mentor-id={mentor.id}
      style={{ "--i": index } as React.CSSProperties}
      className="settle panel p-5"
    >
      <header className="flex items-center gap-3.5">
        <span aria-hidden="true" className="grid size-14 shrink-0 place-items-center rounded-card bg-mint text-lg font-semibold text-signal">
          {avatarText(mentor.name)}
        </span>
        <div className="min-w-0">
          <h3 data-testid="mentor-name" className="truncate text-lg">{mentor.name}</h3>
          <p className="truncate text-sm text-muted">
            {mentor.domain}
            {mentor.company ? ` at ${mentor.company}` : ""}
          </p>
        </div>
      </header>
      <div className="mt-4">
        <EvidenceList mentor={mentor} reasons={reasons} />
      </div>
      <footer className="mt-5 flex flex-wrap gap-2">
        <Link href={`/book/${mentor.id}`} data-testid="book-mentor" className="btn btn-primary">Book a call</Link>
        <Link href={`/mentors/${mentor.id}`} data-testid="view-profile" className="btn btn-quiet">View profile</Link>
      </footer>
    </article>
  );
}
