"use client";
import { useState } from "react";

/** Demo only: shows the private mentor link. In production it is emailed to the mentor. */
export function MentorLink({ token }: { token: string }) {
  const [copied, setCopied] = useState(false);
  const url = `${typeof window === "undefined" ? "" : window.location.origin}/m/${token}`;
  async function copy() {
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  }
  return (
    <div data-testid="demo-mentor-link" className="rounded-card border border-dashed border-brand bg-mint p-4">
      <p className="font-medium">Demo: mentor link</p>
      <p className="mt-1 text-sm">In production this link would be emailed to the mentor. Open it to play the mentor and close the call.</p>
      <div className="mt-3 flex flex-wrap items-center gap-2">
        <a href={`/m/${token}`} data-testid="mentor-link-url" className="break-all font-medium text-signal underline underline-offset-4">{url}</a>
        <button type="button" data-testid="copy-mentor-link" onClick={copy} className="btn btn-quiet">{copied ? "Copied" : "Copy link"}</button>
      </div>
    </div>
  );
}
