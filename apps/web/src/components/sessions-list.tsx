"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { SignIn } from "@/components/sign-in";
import { StatusPill, WriteupPill } from "@/components/status-pill";
import { EmptyState, ErrorState, Loading } from "@/components/states";
import { api } from "@/lib/api";
import { fullLabel } from "@/lib/format";
import { getStudentId, useStudent } from "@/lib/student";
import { useLoad } from "@/lib/use-load";

export function SessionsList() {
  const router = useRouter();
  const { student, ready } = useStudent();
  const { data, error, loading, reload } = useLoad(() => api.listBookings(getStudentId()), ready && student ? student.id : null);
  if (!ready) return <Loading rows={2} />;
  if (!student) return <SignIn lead="Sign in to see your bookings." />;
  if (loading) return <Loading label="Loading sessions" />;
  if (error) return <ErrorState title="Sessions did not load" message={error} onRetry={reload} />;
  if (!data?.length) {
    return <EmptyState title="No sessions yet" body="Once you book a call it shows up here with its status and, after the call, a write-up." href="/" cta="Find a mentor" />;
  }
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[720px] border-collapse text-left">
        <thead>
          <tr className="border-b border-line text-[0.95rem]">
            <th scope="col" className="w-12 py-4 pr-3 font-semibold">#</th>
            <th scope="col" className="py-4 pr-4 font-semibold">Mentor</th>
            <th scope="col" className="py-4 pr-4 font-semibold">Topic / brief</th>
            <th scope="col" className="py-4 pr-4 font-semibold">When</th>
            <th scope="col" className="py-4 font-semibold">Status</th>
          </tr>
        </thead>
        <tbody>
          {data.map((b, i) => (
            <tr
              key={b.id} data-testid="session-row" data-booking-id={b.id}
              onClick={() => router.push(`/sessions/${b.id}`)}
              className="cursor-pointer border-b border-line align-middle transition-colors hover:bg-wash"
            >
              <td className="py-5 pr-3 tnum text-muted">{i + 1}</td>
              <td className="py-5 pr-4">
                <Link href={`/sessions/${b.id}`} className="font-semibold text-signal underline-offset-4 hover:underline" onClick={(e) => e.stopPropagation()}>{b.mentor.name}</Link>
                <span className="block text-sm text-muted">{b.mentor.domain}</span>
              </td>
              <td className="max-w-xs py-5 pr-4 text-[0.95rem]"><span className="line-clamp-2">{b.brief}</span></td>
              <td className="py-5 pr-4 tnum text-[0.95rem]">{fullLabel(b.slot.start)}</td>
              <td className="py-5">
                <div className="flex flex-wrap items-center gap-2">
                  <StatusPill status={b.status} />
                  {b.status === "completed" ? <WriteupPill status={b.writeup_status} /> : null}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
