"use client";
import { ErrorState } from "@/components/states";

export default function Error({ reset }: { error: Error; reset: () => void }) {
  return <div className="page"><ErrorState title="This page hit a problem" message="Reload the page. If it keeps happening, go back to the chat and start again." onRetry={reset} /></div>;
}
