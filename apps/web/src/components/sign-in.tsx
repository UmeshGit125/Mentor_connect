"use client";
import { useState } from "react";
import { api, errorMessage } from "@/lib/api";
import { saveStudent } from "@/lib/student";

export function SignIn({ onDone, lead, bar }: { onDone?: () => void; lead?: string; bar?: boolean }) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const s = await api.createStudent(name.trim(), email.trim());
      saveStudent(s);
      onDone?.();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  if (bar) {
    // Search-bar style for the home hero: name, email and one green action in a single row.
    return (
      <form onSubmit={submit} data-testid="signin-form" aria-label="Tell us who you are">
        <div className="flex flex-col gap-2 rounded-card border border-line bg-white p-2 shadow-card md:flex-row md:items-center md:gap-0 md:p-2.5">
          <label htmlFor="su-name" className="sr-only">Name</label>
          <input id="su-name" data-testid="signin-name" name="name" autoComplete="name" required placeholder="Your name" value={name} onChange={(e) => setName(e.target.value)} className="min-h-[52px] flex-1 bg-transparent px-4 text-[0.95rem] outline-none placeholder:text-[#8a929b] md:border-r md:border-line" />
          <label htmlFor="su-email" className="sr-only">Email</label>
          <input id="su-email" data-testid="signin-email" name="email" type="email" autoComplete="email" spellCheck={false} required placeholder="Your email" value={email} onChange={(e) => setEmail(e.target.value)} className="min-h-[52px] flex-1 bg-transparent px-4 text-[0.95rem] outline-none placeholder:text-[#8a929b]" />
          <button type="submit" data-testid="signin-submit" disabled={busy} className="btn btn-primary !min-h-[52px] shrink-0 !px-8 uppercase tracking-wide">
            {busy ? "Saving…" : "Continue"}
          </button>
        </div>
        <p className="mt-3 text-sm text-muted">{lead ?? "Start with your name and email so we can keep your chats and bookings together. No password needed."}</p>
        {error ? <p role="alert" data-testid="signin-error" className="mt-2 text-sm font-medium text-danger">{error}</p> : null}
      </form>
    );
  }

  return (
    <form onSubmit={submit} data-testid="signin-form" className="panel space-y-4 p-5 md:p-6">
      <div>
        <h2 className="text-xl font-semibold">Tell us who you are</h2>
        <p className="mt-1 text-sm text-muted">{lead ?? "We use this to keep your chats and bookings together. No password needed."}</p>
      </div>
      <div>
        <label htmlFor="su-name" className="mb-1.5 block text-sm font-medium">Name</label>
        <input id="su-name" data-testid="signin-name" name="name" autoComplete="name" required value={name} onChange={(e) => setName(e.target.value)} className="field" />
      </div>
      <div>
        <label htmlFor="su-email" className="mb-1.5 block text-sm font-medium">Email</label>
        <input id="su-email" data-testid="signin-email" name="email" type="email" autoComplete="email" spellCheck={false} required value={email} onChange={(e) => setEmail(e.target.value)} className="field" />
      </div>
      {error ? <p role="alert" data-testid="signin-error" className="text-sm font-medium text-danger">{error}</p> : null}
      <button type="submit" data-testid="signin-submit" disabled={busy} className="btn btn-primary w-full sm:w-auto">
        {busy ? "Saving…" : "Continue"}
      </button>
    </form>
  );
}
