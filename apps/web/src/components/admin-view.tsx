"use client";
import { useEffect, useState } from "react";
import { StatusPill } from "@/components/status-pill";
import { EmptyState, ErrorState, Loading } from "@/components/states";
import { api, ApiError, errorMessage } from "@/lib/api";
import { fullLabel } from "@/lib/format";
import type { AdminSummary } from "@/lib/types";

const KEY = "mc_admin_pw";
// The password lives only in sessionStorage and is guarded against storage errors.
const readPw = () => { try { return window.sessionStorage.getItem(KEY); } catch { return null; } };
const writePw = (v: string | null) => { try { if (v) window.sessionStorage.setItem(KEY, v); else window.sessionStorage.removeItem(KEY); } catch { /* memory only */ } };

const FUNNEL: [keyof AdminSummary["funnel"], string][] = [
  ["chats_started", "Chats started"], ["matched", "Matched"], ["booked", "Booked"],
  ["completed", "Completed"], ["writeups_ready", "Write-ups ready"], ["rebooked", "Rebooked"],
];

export function AdminView() {
  const [pw, setPw] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [data, setData] = useState<AdminSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [checked, setChecked] = useState(false);
  const [updated, setUpdated] = useState<Date | null>(null);

  async function load(password: string) {
    setBusy(true);
    setError(null);
    try {
      setData(await api.adminSummary(password));
      setUpdated(new Date());
      writePw(password);
      setPw(password);
    } catch (e) {
      if (e instanceof ApiError && e.code === "unauthorized") writePw(null);
      setPw(null);
      setError(errorMessage(e));
    } finally {
      setBusy(false);
      setChecked(true);
    }
  }

  useEffect(() => {
    const saved = readPw();
    if (saved) void load(saved);
    else setChecked(true);
  }, []);

  // Keep the numbers current: a quiet refetch every 15s and whenever the tab becomes visible again.
  useEffect(() => {
    if (!pw) return;
    const tick = async () => {
      if (document.visibilityState !== "visible") return;
      try {
        setData(await api.adminSummary(pw));
        setUpdated(new Date());
        setError(null);
      } catch (e) {
        setError(errorMessage(e));
      }
    };
    const id = window.setInterval(tick, 15000);
    document.addEventListener("visibilitychange", tick);
    return () => { window.clearInterval(id); document.removeEventListener("visibilitychange", tick); };
  }, [pw]);

  if (!checked) return <Loading rows={2} />;

  if (!data || !pw) {
    return (
      <form onSubmit={(e) => { e.preventDefault(); void load(input); }} data-testid="admin-gate" className="panel mx-auto max-w-md space-y-4 p-6">
        <h1 className="h-page">Admin</h1>
        <div>
          <label htmlFor="pw" className="mb-1.5 block text-sm font-medium">Password</label>
          <input id="pw" name="password" data-testid="admin-password" type="password" autoComplete="current-password" required value={input} onChange={(e) => setInput(e.target.value)} className="field" />
        </div>
        {error ? <p role="alert" data-testid="admin-error" className="font-medium text-danger">{error}</p> : null}
        <button type="submit" data-testid="admin-submit" disabled={busy} className="btn btn-primary">{busy ? "Checking…" : "Open dashboard"}</button>
      </form>
    );
  }

  const s = data;
  const statuses = Object.entries(s.bookings_by_status) as [keyof typeof s.bookings_by_status, number][];
  return (
    <div className="space-y-12">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="h-page">Admin</h1>
          {updated ? <p className="mt-1 text-sm text-muted">Updated {updated.toLocaleTimeString()}. Refreshes every 15 seconds.</p> : null}
        </div>
        <div className="flex gap-2">
          <button type="button" onClick={() => load(pw)} disabled={busy} className="btn btn-quiet">Refresh</button>
          <button type="button" onClick={() => { writePw(null); setPw(null); setData(null); setInput(""); }} className="btn btn-quiet">Lock</button>
        </div>
      </div>
      {error ? <ErrorState title="Refresh failed" message={error} /> : null}

      <section aria-labelledby="funnel-h">
        <h2 id="funnel-h" className="text-xl">Funnel</h2>
        <dl className="mt-3 grid grid-cols-2 gap-2 md:grid-cols-6">
          {FUNNEL.map(([k, label]) => (
            <div key={k} className="panel p-4">
              <dt className="text-sm text-muted">{label}</dt>
              <dd data-testid={`funnel-${k}`} className="mt-1 text-3xl font-bold text-signal tnum">{s.funnel[k]}</dd>
            </div>
          ))}
        </dl>
      </section>

      <section aria-labelledby="status-h">
        <h2 id="status-h" className="text-xl">Bookings by status</h2>
        <ul className="mt-3 flex flex-wrap gap-3">
          {statuses.map(([k, n]) => (
            <li key={k} className="flex items-center gap-2"><StatusPill status={k} /><span data-testid={`status-count-${k}`} className="tnum font-medium">{n}</span></li>
          ))}
        </ul>
      </section>

      <section aria-labelledby="stuck-h" className="space-y-3">
        <h2 id="stuck-h" className="text-xl">Stuck bookings</h2>
        {s.stuck.length ? (
          <ul data-testid="stuck-list" className="space-y-2">
            {s.stuck.map((b) => (
              <li key={b.id} data-testid="stuck-row" className="rounded-card border border-danger/40 bg-danger-wash p-4">
                <p className="font-medium">{b.mentor.name} <span className="tnum font-normal">on {fullLabel(b.slot.start)}</span></p>
                <p className="text-sm">Still confirmed two or more days after the slot ended. Ask the mentor to close it.</p>
              </li>
            ))}
          </ul>
        ) : <EmptyState title="Nothing stuck" body="Every past call has been closed." />}
      </section>

      <section aria-labelledby="unmatched-h" className="space-y-3">
        <h2 id="unmatched-h" className="text-xl">Unmatched problems</h2>
        {s.unmatched.length ? (
          <ul data-testid="unmatched-list" className="space-y-2">
            {s.unmatched.map((u) => (
              <li key={u.id} data-testid="unmatched-row" className="rounded-card border border-danger/40 bg-danger-wash p-4">
                <p>{u.summary}</p>
                <p className="text-sm tnum text-muted">{fullLabel(u.created_at)}</p>
              </li>
            ))}
          </ul>
        ) : <EmptyState title="No unmatched chats" body="Every chat so far found at least one mentor." />}
      </section>

      <section aria-labelledby="load-h" className="space-y-3">
        <h2 id="load-h" className="text-xl">Mentor load</h2>
        {s.mentor_load.length ? (
          <div className="overflow-x-auto panel">
            <table className="w-full text-left" data-testid="mentor-load">
              <thead className="text-sm text-muted"><tr><th scope="col" className="p-3 font-medium">Mentor</th><th scope="col" className="p-3 font-medium">Active</th><th scope="col" className="p-3 font-medium">Completed</th></tr></thead>
              <tbody>
                {s.mentor_load.map((m) => (
                  <tr key={m.mentor_id} className="border-t border-line">
                    <th scope="row" className="p-3 font-medium">{m.name}</th>
                    <td className="p-3 tnum">{m.active}</td>
                    <td className="p-3 tnum">{m.completed}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : <EmptyState title="No mentor activity" body="Bookings will show here by mentor." />}
      </section>
    </div>
  );
}
