/** Quiet geometric background for the hero: faint zig-zag lines plus a few green shapes. SVG only. */
export function HeroArt() {
  return (
    <div aria-hidden="true" className="pointer-events-none absolute inset-0">
      <svg className="absolute inset-0 h-full w-full" preserveAspectRatio="xMidYMid slice" viewBox="0 0 1440 700" fill="none">
        <defs>
          <pattern id="zig" width="220" height="140" patternUnits="userSpaceOnUse" patternTransform="rotate(-24)">
            <path d="M0 40h70l30 30h120M0 110h90l30-30h100" stroke="#eef1f0" strokeWidth="2" />
          </pattern>
          <linearGradient id="fade" x1="0" x2="1" y1="0" y2="0">
            <stop offset="0" stopColor="#fff" stopOpacity="1" />
            <stop offset="0.45" stopColor="#fff" stopOpacity="0.2" />
            <stop offset="1" stopColor="#fff" stopOpacity="0" />
          </linearGradient>
        </defs>
        <rect width="1440" height="700" fill="url(#zig)" />
        <rect width="1440" height="700" fill="url(#fade)" />
        <circle cx="1230" cy="150" r="64" fill="#e9f9f2" />
        <circle cx="1330" cy="300" r="14" fill="#17ce85" opacity="0.8" />
        <circle cx="1120" cy="420" r="26" stroke="#0dbb7c" strokeWidth="2" opacity="0.5" />
        <path d="M1250 520l36-20 36 20v40l-36 20-36-20z" stroke="#c9ece0" strokeWidth="2" />
        <rect x="1040" y="90" width="44" height="44" rx="6" stroke="#c9ece0" strokeWidth="2" transform="rotate(14 1062 112)" />
        <circle cx="1380" cy="560" r="40" fill="#e9f9f2" />
      </svg>
    </div>
  );
}
