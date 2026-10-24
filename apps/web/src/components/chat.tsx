"use client";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { HeroArt } from "@/components/hero-art";
import { RecommendationCard } from "@/components/recommendation-card";
import { SignIn } from "@/components/sign-in";
import { api, errorMessage } from "@/lib/api";
import { rememberChatSession } from "@/lib/chat-session";
import { getStudentId, useStudent } from "@/lib/student";
import type { ChatReply, Match } from "@/lib/types";

type Msg = { role: "student" | "assistant"; text: string; kind?: ChatReply["kind"] };

const EXAMPLES = [
  "I'm a final-year BCom student and want to move into fintech product roles",
  "I know Excel but not SQL. How do I become a data analyst?",
  "I want to get into marketing but have no internships",
  "I'm confused between consulting and a startup job",
];

export function Chat({ below }: { below?: React.ReactNode }) {
  const { student, ready } = useStudent();
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [sid, setSid] = useState<string | null>(null);
  const [draft, setDraft] = useState("");
  const [matches, setMatches] = useState<Match[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [failed, setFailed] = useState<string | null>(null);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ block: "nearest" });
  }, [msgs, matches, busy]);

  async function send(text: string) {
    const clean = text.trim();
    if (!clean || busy) return;
    setMsgs((m) => [...m, { role: "student", text: clean }]);
    setDraft("");
    setError(null);
    setFailed(null);
    setBusy(true);
    try {
      const r = await api.chat(sid, clean, getStudentId());
      setSid(r.session_id);
      rememberChatSession(r.session_id);
      setMsgs((m) => [...m, { role: "assistant", text: r.message, kind: r.kind }]);
      if (r.kind === "matches") setMatches(r.matches);
    } catch (e) {
      setError(errorMessage(e));
      setFailed(clean);
    } finally {
      setBusy(false);
    }
  }

  function pickExample(text: string) {
    if (student) void send(text);
    else setDraft(text);
  }

  const empty = msgs.length === 0;

  const composer = !ready ? null : student ? (
    <form
      onSubmit={(e) => { e.preventDefault(); void send(draft); }}
      className="flex items-end gap-3 rounded-card border border-line bg-white p-3 shadow-card focus-within:border-brand focus-within:shadow-[0_0_0_3px_rgba(13,187,124,0.2)]"
    >
      <label htmlFor="chat-input" className="sr-only">Describe where you are stuck</label>
      <textarea
        id="chat-input" name="message" autoComplete="off" data-testid="chat-input" rows={2} maxLength={2000} value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); void send(draft); } }}
        placeholder="Describe where you are stuck…" className="min-h-[3.25rem] w-full resize-none bg-transparent px-3 py-2.5 text-[0.95rem] outline-none placeholder:text-[#8a929b]"
      />
      <button type="submit" data-testid="chat-send" disabled={busy || !draft.trim()} className="btn btn-primary !min-h-[52px] shrink-0 !px-8 uppercase tracking-wide">Send</button>
    </form>
  ) : (
    <SignIn bar={empty} lead={draft ? "Sign in to send your message. It is saved." : undefined} onDone={() => { if (draft) void send(draft); }} />
  );

  const examples = (
    <ul data-testid="chat-empty" className="flex flex-wrap gap-2">
      {EXAMPLES.map((ex, i) => (
        <li key={ex}>
          <button type="button" data-testid={`example-${i}`} onClick={() => pickExample(ex)} className="chip text-left">
            {ex}
          </button>
        </li>
      ))}
    </ul>
  );

  if (empty) {
    return (
      <>
        <section aria-labelledby="hero-h" className="relative overflow-hidden">
          <HeroArt />
          <div className="wrap relative pb-20 pt-12 md:pb-28 md:pt-20">
            <h1 id="hero-h" className="max-w-[640px] text-[clamp(2.4rem,5vw,3.5rem)] leading-[1.13]">Get matched with the right mentor</h1>
            <p className="mt-6 max-w-[560px] text-base leading-8 text-muted md:text-[1.05rem]">
              Describe where you are stuck in your own words. We pick up to three mentors from our list of 50 and show the exact profile details behind each pick.
            </p>
            <div className="mt-10 max-w-[900px]">{composer}</div>
            <p className="mb-3 mt-6 text-sm font-medium text-muted">Popular starting points</p>
            <div className="max-w-[900px]">{examples}</div>
          </div>
        </section>
        {below}
      </>
    );
  }

  return (
    <div className="wrap pb-20 pt-8">
      <div className="chat-grid">
        <section className="chat-conv min-w-0" aria-label="Conversation">
          <div role="log" aria-live="polite" aria-label="Messages" data-testid="chat-log" className="space-y-3">
            {msgs.map((m, i) => (
              <div
                key={i} data-testid={`msg-${m.role}`} data-kind={m.kind}
                className={m.role === "student"
                  ? "ml-auto w-fit max-w-[85%] rounded-card rounded-br-none bg-brand px-5 py-3 font-medium text-white"
                  : "max-w-[92%] measure rounded-card rounded-bl-none border border-line bg-white px-5 py-3 shadow-card"}
              >
                <p className="whitespace-pre-wrap leading-7">{m.text}</p>
                {m.kind === "no_match" ? (
                  <Link href="/mentors" className="mt-2 inline-block font-semibold text-signal underline underline-offset-4">Browse all mentors</Link>
                ) : null}
              </div>
            ))}
            {busy ? (
              <div data-testid="chat-typing" role="status" className="w-fit rounded-card rounded-bl-none border border-line bg-white px-5 py-3 text-muted shadow-card">Finding mentors…</div>
            ) : null}
          </div>
          {error ? (
            <div role="alert" data-testid="chat-error" className="mt-3 rounded-card border border-danger/40 bg-danger-wash p-4">
              <p>{error}</p>
              {failed ? (
                <button type="button" data-testid="chat-retry" onClick={() => { setMsgs((m) => m.slice(0, -1)); void send(failed); }} className="btn btn-quiet mt-3">
                  Send again
                </button>
              ) : null}
            </div>
          ) : null}
          <div ref={endRef} />
        </section>

        <aside className="chat-panel min-w-0" aria-label="Mentors for you">
          <h2 className="mb-4 text-2xl">Mentors for you</h2>
          {matches.length ? (
            <div data-testid="match-panel" className="space-y-4">
              {matches.map((m, i) => (
                <RecommendationCard key={m.mentor.id} match={m} index={i} />
              ))}
            </div>
          ) : (
            <div data-testid="match-empty" className="rounded-card border border-dashed border-[#c6cfce] bg-wash p-5 text-muted">
              <p>Up to three mentors show here once you describe what you need. Each one comes with the profile details that make it a fit.</p>
            </div>
          )}
        </aside>

        <div className="chat-form">{composer}</div>
      </div>
    </div>
  );
}
