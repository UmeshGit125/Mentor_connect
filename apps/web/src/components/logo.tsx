import Link from "next/link";

/** Our own wordmark: two dots and a green sweep, then the name. */
export function Logo({ className = "", href = "/" }: { className?: string; href?: string }) {
  return (
    <Link href={href} aria-label={href === "/" ? "Mentor Connect home" : "Mentor Connect admin"} className={`inline-flex items-center gap-2.5 ${className}`}>
      <svg aria-hidden="true" width="34" height="34" viewBox="0 0 34 34" fill="none">
        <circle cx="9" cy="7" r="4.5" fill="#8c9296" />
        <circle cx="26" cy="7" r="4.5" fill="#0dbb7c" />
        <path d="M5 15c0 7 4.5 13 11.5 13S29 21 29 14c-3 5-7.5 8-12 8-6 0-9-3-12-7z" fill="#0dbb7c" />
        <path d="M5 15c1.5 2.5 3.5 4.5 6 5.5C8 20 5 17.5 5 15z" fill="#8c9296" />
      </svg>
      <span className="text-[1.15rem] font-bold leading-none tracking-tight text-ink">
        Mentor <span className="text-signal">Connect</span>
      </span>
    </Link>
  );
}
