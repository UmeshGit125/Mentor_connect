"use client";
import { useMemo, useState } from "react";
import { dayKey, dayLabel, timeLabel, TZ_NOTE } from "@/lib/format";
import type { Slot } from "@/lib/types";

export function SlotPicker({ slots, selected, onSelect, disabled }: { slots: Slot[]; selected: string | null; onSelect: (id: string) => void; disabled?: boolean }) {
  const days = useMemo(() => {
    const map = new Map<string, Slot[]>();
    for (const s of slots.filter((x) => x.status === "open")) {
      const k = dayKey(s.start);
      map.set(k, [...(map.get(k) ?? []), s]);
    }
    return [...map.entries()];
  }, [slots]);
  const selectedDay = slots.find((s) => s.id === selected);
  const [day, setDay] = useState<string | null>(null);
  const active = day ?? (selectedDay ? dayKey(selectedDay.start) : days[0]?.[0]);

  if (!days.length) {
    return (
      <div data-testid="slots-empty" className="rounded-card border border-dashed border-[#c6cfce] bg-wash p-5 text-muted">
        No open times in the next 7 days. Check again tomorrow or pick another mentor.
      </div>
    );
  }

  const todays = days.find(([k]) => k === active)?.[1] ?? [];
  return (
    <div>
      <div role="group" aria-label="Pick a day" className="-mx-1 flex gap-2 overflow-x-auto px-1 pb-1">
        {days.map(([k, list]) => (
          <button
            key={k} type="button" data-testid="day-tab" aria-pressed={k === active} onClick={() => setDay(k)}
            className={`shrink-0 rounded-control border px-3 py-2 text-left ${k === active ? "border-brand bg-brand text-white" : "border-line bg-white hover:border-brand"}`}
          >
            <span className="block text-sm font-medium">{dayLabel(list[0].start)}</span>
            <span className={`block text-xs tnum ${k === active ? "text-white/90" : "text-muted"}`}>{list.length} open</span>
          </button>
        ))}
      </div>
      <ul className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-3">
        {todays.map((s) => (
          <li key={s.id}>
            <button
              type="button" data-testid="slot" data-slot-id={s.id} aria-pressed={s.id === selected} disabled={disabled}
              onClick={() => onSelect(s.id)}
              className={`btn w-full tnum ${s.id === selected ? "btn-primary" : "btn-quiet"}`}
            >
              {timeLabel(s.start)}
            </button>
          </li>
        ))}
      </ul>
      <p className="mt-3 text-sm text-muted">{TZ_NOTE}. Each call is 30 minutes.</p>
    </div>
  );
}
