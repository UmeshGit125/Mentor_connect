"use client";
import { useId, useState } from "react";

export type Faq = { q: string; a: string };

/** Single-open accordion. Each question is a real button with aria-expanded and aria-controls. */
export function FaqList({ items }: { items: Faq[] }) {
  const base = useId();
  const [open, setOpen] = useState<number | null>(null);
  return (
    <ul className="space-y-5">
      {items.map((f, i) => {
        const isOpen = open === i;
        return (
          <li key={f.q} className="panel">
            <h2 className="text-base">
              <button
                type="button" id={`${base}-b${i}`} aria-expanded={isOpen} aria-controls={`${base}-p${i}`}
                onClick={() => setOpen(isOpen ? null : i)}
                className="flex w-full items-center justify-between gap-4 px-7 py-6 text-left text-[1.05rem] font-semibold"
              >
                {f.q}
                <span aria-hidden="true" className="acc-icon" />
              </button>
            </h2>
            <div id={`${base}-p${i}`} role="region" aria-labelledby={`${base}-b${i}`} hidden={!isOpen} className="px-7 pb-6 leading-7 text-muted">
              <p>{f.a}</p>
            </div>
          </li>
        );
      })}
    </ul>
  );
}
