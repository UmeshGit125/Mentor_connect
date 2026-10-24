const TZ = "Asia/Kolkata";

export function dayKey(iso: string): string {
  return new Intl.DateTimeFormat("en-CA", { timeZone: TZ }).format(new Date(iso));
}

export function dayLabel(iso: string): string {
  return new Intl.DateTimeFormat("en-IN", { timeZone: TZ, weekday: "short", day: "numeric", month: "short" }).format(
    new Date(iso),
  );
}

export function timeLabel(iso: string): string {
  return new Intl.DateTimeFormat("en-IN", { timeZone: TZ, hour: "numeric", minute: "2-digit", hour12: true }).format(
    new Date(iso),
  );
}

export function fullLabel(iso: string): string {
  return `${dayLabel(iso)}, ${timeLabel(iso)} IST`;
}

export const TZ_NOTE = "Times shown in India Standard Time (IST)";

export function initials(name: string): string {
  // Letters only, so "Mentor 009" gives "M" plus the next letter rather than a digit.
  const words = name.split(/\s+/).map((w) => w.replace(/[^\p{L}]/gu, "")).filter(Boolean);
  if (words.length > 1) return (words[0][0] + words[1][0]).toUpperCase();
  return (words[0] ?? "").slice(0, 2).toUpperCase();
}

/** Avatar text: the mentor number when the name carries one ("Mentor 021" gives "021"), otherwise initials. */
export function avatarText(name: string): string {
  return name.match(/\d+/)?.[0] ?? initials(name);
}
