"use client";
import Link from "next/link";
import { SlotPicker } from "@/components/slot-picker";
import { Loading, ErrorState } from "@/components/states";
import { api } from "@/lib/api";
import { useLoad } from "@/lib/use-load";
import { useState } from "react";

/** Slots on the profile page. Picking a time carries on to the booking page. */
export function MentorSlots({ mentorId }: { mentorId: string }) {
  const { data, error, loading, reload } = useLoad(() => api.getSlots(mentorId), mentorId);
  const [sel, setSel] = useState<string | null>(null);
  if (loading) return <Loading rows={2} label="Loading times" />;
  if (error) return <ErrorState title="Times did not load" message={error} onRetry={reload} />;
  return (
    <div className="space-y-4">
      <SlotPicker slots={data ?? []} selected={sel} onSelect={setSel} />
      <Link
        href={sel ? `/book/${mentorId}?slot=${encodeURIComponent(sel)}` : `/book/${mentorId}`}
        data-testid="continue-booking" className="btn btn-primary"
      >
        {sel ? "Continue with this time" : "Go to booking"}
      </Link>
    </div>
  );
}
