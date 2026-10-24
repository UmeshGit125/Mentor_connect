"use client";
import { useState } from "react";
import { api, errorMessage } from "@/lib/api";

type Errors = Partial<Record<"name" | "email" | "message", string>>;

export function ContactForm() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [errors, setErrors] = useState<Errors>({});
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<{ ok: boolean; text: string } | null>(null);

  function validate(): Errors {
    const e: Errors = {};
    if (!name.trim()) e.name = "Enter your full name.";
    if (!email.trim()) e.email = "Enter your email.";
    else if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email.trim())) e.email = "Enter a valid email, like name@example.com.";
    if (!message.trim()) e.message = "Write a short message.";
    return e;
  }

  async function submit(ev: React.FormEvent) {
    ev.preventDefault();
    setNotice(null);
    const e = validate();
    setErrors(e);
    if (Object.keys(e).length) return;
    setBusy(true);
    try {
      await api.sendContact(name.trim(), email.trim(), message.trim());
      setNotice({ ok: true, text: "Thank you. We have received your message and will reply by email." });
      setName(""); setEmail(""); setMessage("");
    } catch (err) {
      setNotice({ ok: false, text: errorMessage(err) });
    } finally {
      setBusy(false);
    }
  }

  const err = (id: string, text?: string) => (text ? <p id={id} className="mt-1.5 text-sm font-medium text-danger">{text}</p> : null);
  return (
    <form onSubmit={submit} noValidate data-testid="contact-form" className="mx-auto max-w-[620px] space-y-6">
      <div className="grid gap-6 sm:grid-cols-2">
        <div>
          <label htmlFor="c-name" className="mb-2 block text-[0.95rem] font-medium">Your full name</label>
          <input id="c-name" name="name" autoComplete="name" value={name} onChange={(e) => setName(e.target.value)} aria-invalid={!!errors.name} aria-describedby={errors.name ? "c-name-e" : undefined} data-testid="contact-name" className="field" />
          {err("c-name-e", errors.name)}
        </div>
        <div>
          <label htmlFor="c-email" className="mb-2 block text-[0.95rem] font-medium">Your email</label>
          <input id="c-email" name="email" type="email" autoComplete="email" spellCheck={false} value={email} onChange={(e) => setEmail(e.target.value)} aria-invalid={!!errors.email} aria-describedby={errors.email ? "c-email-e" : undefined} data-testid="contact-email" className="field" />
          {err("c-email-e", errors.email)}
        </div>
      </div>
      <div>
        <label htmlFor="c-msg" className="mb-2 block text-[0.95rem] font-medium">Message</label>
        <textarea id="c-msg" name="message" rows={6} maxLength={4000} placeholder="Write more details" value={message} onChange={(e) => setMessage(e.target.value)} aria-invalid={!!errors.message} aria-describedby={errors.message ? "c-msg-e" : undefined} data-testid="contact-message" className="field resize-y" />
        {err("c-msg-e", errors.message)}
      </div>
      <button type="submit" disabled={busy} data-testid="contact-submit" className="btn btn-quiet !px-7">
        {busy ? "Sending…" : "Submit"}
      </button>
      <div role="status" aria-live="polite" data-testid="contact-notice">
        {notice ? (
          <p className={`rounded-card border p-4 font-medium ${notice.ok ? "border-brand/40 bg-mint text-signal" : "border-danger/40 bg-danger-wash text-danger"}`}>{notice.text}</p>
        ) : null}
      </div>
    </form>
  );
}
