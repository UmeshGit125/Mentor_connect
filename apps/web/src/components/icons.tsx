/** Small line icons, drawn inline. Stroke follows currentColor. */
const base = { width: 28, height: 28, viewBox: "0 0 28 28", fill: "none", stroke: "currentColor", strokeWidth: 1.7, strokeLinecap: "round", strokeLinejoin: "round", "aria-hidden": true } as const;

export const ICONS = {
  compass: <svg {...base}><circle cx="14" cy="14" r="9.5" /><path d="M17.8 10.2l-2.1 5.5-5.5 2.1 2.1-5.5z" /></svg>,
  layers: <svg {...base}><path d="M14 4.5l9.5 5-9.5 5-9.5-5z" /><path d="M4.5 14l9.5 5 9.5-5M4.5 18.5l9.5 5 9.5-5" /></svg>,
  box: <svg {...base}><path d="M14 4l9 4.8v10.4L14 24l-9-4.8V8.8z" /><path d="M5 8.8l9 4.8 9-4.8M14 13.6V24" /></svg>,
  chart: <svg {...base}><path d="M5 22.5V5.5M5 22.5h18" /><path d="M9.5 18l4-5 3.5 3 5-7" /></svg>,
  pen: <svg {...base}><path d="M5 23l1-5L18.5 5.5a2.1 2.1 0 013 3L9 21z" /><path d="M16.5 7.5l3 3" /></svg>,
  tree: <svg {...base}><circle cx="14" cy="6" r="2.5" /><circle cx="6" cy="21" r="2.5" /><circle cx="14" cy="21" r="2.5" /><circle cx="22" cy="21" r="2.5" /><path d="M14 8.5V13M6 18.5V13h16v5.5" /></svg>,
  people: <svg {...base}><circle cx="14" cy="9" r="3.5" /><path d="M6.5 22c.6-4.3 3.5-6.5 7.5-6.5s6.9 2.2 7.5 6.5" /></svg>,
  case: <svg {...base}><rect x="4" y="8.5" width="20" height="14" rx="2.2" /><path d="M10 8.5V6.2c0-.7.6-1.2 1.2-1.2h5.6c.6 0 1.2.5 1.2 1.2v2.3M4 14.5h20" /></svg>,
  search: <svg {...base}><circle cx="12.5" cy="12.5" r="7.5" /><path d="M18 18l5 5" /></svg>,
  calendar: <svg {...base}><rect x="4.5" y="6" width="19" height="17" rx="2.2" /><path d="M9.5 3.5v5M18.5 3.5v5M4.5 12h19" /></svg>,
  note: <svg {...base}><path d="M7 4.5h14a1 1 0 011 1v17a1 1 0 01-1 1H7a1 1 0 01-1-1v-17a1 1 0 011-1z" /><path d="M10 10h8M10 14h8M10 18h5" /></svg>,
  shield: <svg {...base}><path d="M14 4l8 3v6.5c0 5-3.3 8.4-8 10.5-4.7-2.1-8-5.5-8-10.500V7z" /><path d="M10.5 14l2.5 2.5 4.5-5" /></svg>,
  bars: <svg {...base}><path d="M5 23V14M11 23V8M17 23v-6M23 23V5" /></svg>,
  badge: <svg {...base}><circle cx="14" cy="11" r="6.5" /><path d="M10.5 16.500L9 24l5-2.5 5 2.5-1.5-7.5" /></svg>,
} as const;

export type IconName = keyof typeof ICONS;
export const CATEGORY_ICONS: IconName[] = ["compass", "layers", "box", "chart", "pen", "tree", "people", "case"];
