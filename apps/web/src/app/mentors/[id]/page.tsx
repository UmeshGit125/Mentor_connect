import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ErrorState } from "@/components/states";
import { MentorFacts } from "@/components/mentor-facts";
import { MentorSlots } from "@/components/mentor-slots";
import { api, ApiError, errorMessage } from "@/lib/api";
import { avatarText } from "@/lib/format";

export const dynamic = "force-dynamic";

export async function generateMetadata({ params }: { params: Promise<{ id: string }> }): Promise<Metadata> {
  const { id } = await params;
  try {
    return { title: (await api.getMentor(id)).name };
  } catch {
    return { title: "Mentor" };
  }
}

export default async function MentorPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  let mentor;
  try {
    mentor = await api.getMentor(id);
  } catch (e) {
    if (e instanceof ApiError && e.code === "not_found") notFound();
    return <div className="page"><ErrorState title="Profile did not load" message={`${errorMessage(e)} Refresh the page to try again.`} /></div>;
  }
  return (
    <div className="page space-y-10">
      <Link href="/mentors" className="inline-block text-sm font-medium text-signal underline-offset-4 hover:underline">← All mentors</Link>
      <header className="panel flex flex-wrap items-center gap-5 p-5 md:p-6">
        <span aria-hidden="true" className="grid size-24 place-items-center rounded-card bg-mint text-3xl font-semibold text-signal">{avatarText(mentor.name)}</span>
        <div className="min-w-0 flex-1">
          <h1 data-testid="mentor-name" className="h-page">{mentor.name}</h1>
          <p className="mt-1 text-muted">{mentor.domain}{mentor.company ? ` at ${mentor.company}` : ""}</p>
        </div>
      </header>
      <section aria-labelledby="facts-h" className="space-y-4">
        <h2 id="facts-h" className="text-xl">From their profile</h2>
        <MentorFacts mentor={mentor} />
      </section>
      <section aria-labelledby="slots-h" className="space-y-4">
        <h2 id="slots-h" className="text-xl">Open times this week</h2>
        <MentorSlots mentorId={mentor.id} />
      </section>
    </div>
  );
}
