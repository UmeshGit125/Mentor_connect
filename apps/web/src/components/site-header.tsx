"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useId, useRef, useState } from "react";
import { Logo } from "@/components/logo";
import { StudentBadge } from "@/components/student-badge";
import { useStudent } from "@/lib/student";

const LINKS = [
  { href: "/", label: "Home", match: (p: string) => p === "/" || p.startsWith("/chat") },
  { href: "/mentors", label: "Mentors", match: (p: string) => p.startsWith("/mentors") || p.startsWith("/book") },
  { href: "/sessions", label: "My sessions", match: (p: string) => p.startsWith("/sessions") },
  { href: "/faqs", label: "FAQs", match: (p: string) => p.startsWith("/faqs") },
  { href: "/contact", label: "Contact", match: (p: string) => p.startsWith("/contact") },
];
const PAGES = [
  { href: "/terms", label: "Terms and Condition" },
  { href: "/privacy", label: "Privacy Policy" },
];

function Chevron({ open }: { open: boolean }) {
  return (
    <svg aria-hidden="true" width="11" height="7" viewBox="0 0 12 8" className={`transition-transform ${open ? "rotate-180" : ""}`}>
      <path d="M1 1.5l5 5 5-5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function PagesMenu({ pathname }: { pathname: string }) {
  const [open, setOpen] = useState(false);
  const box = useRef<HTMLDivElement>(null);
  const id = useId();
  const [seen, setSeen] = useState(pathname);
  // Close on route change (state adjusted during render, not in an effect).
  if (seen !== pathname) {
    setSeen(pathname);
    setOpen(false);
  }

  useEffect(() => {
    if (!open) return;
    const away = (e: MouseEvent) => { if (!box.current?.contains(e.target as Node)) setOpen(false); };
    const esc = (e: KeyboardEvent) => { if (e.key === "Escape") { setOpen(false); box.current?.querySelector("button")?.focus(); } };
    const tab = (e: FocusEvent) => { if (!box.current?.contains(e.target as Node)) setOpen(false); };
    document.addEventListener("mousedown", away);
    document.addEventListener("keydown", esc);
    document.addEventListener("focusin", tab);
    return () => {
      document.removeEventListener("mousedown", away);
      document.removeEventListener("keydown", esc);
      document.removeEventListener("focusin", tab);
    };
  }, [open]);

  const active = PAGES.some((p) => pathname.startsWith(p.href));
  return (
    <div ref={box} className="relative">
      <button
        type="button" aria-expanded={open} aria-controls={id} onClick={() => setOpen((o) => !o)}
        className={`nav-link inline-flex items-center gap-1.5 ${active || open ? "!text-signal" : ""}`}
      >
        Pages <Chevron open={open} />
      </button>
      <div
        id={id} hidden={!open}
        className="absolute left-1/2 top-full z-50 mt-2 w-56 -translate-x-1/2 rounded-card border border-line bg-white p-2 shadow-lift"
      >
        {PAGES.map((p) => (
          <Link key={p.href} href={p.href} className="block rounded-[4px] px-3 py-2.5 text-sm text-muted transition-colors hover:bg-mint hover:text-signal">
            {p.label}
          </Link>
        ))}
      </div>
    </div>
  );
}

export function SiteHeader() {
  const pathname = usePathname();
  const { student, ready } = useStudent();
  const [menu, setMenu] = useState(false);
  const [seen, setSeen] = useState(pathname);
  if (seen !== pathname) {
    setSeen(pathname);
    setMenu(false);
  }
  const signedOut = ready && !student;

  // The admin area gets its own bare header so no student link can pull an admin out of it.
  if (pathname.startsWith("/admin")) {
    return (
      <header className="sticky top-0 z-40 border-b border-line bg-white/95 backdrop-blur">
        <div className="wrap flex h-[76px] items-center gap-4">
          <Logo href="/admin" />
          <span className="rounded-control bg-mint px-3 py-1 text-sm font-semibold text-signal">Admin</span>
        </div>
      </header>
    );
  }

  return (
    <header className="sticky top-0 z-40 border-b border-line bg-white/95 backdrop-blur">
      <div className="wrap flex h-[76px] items-center gap-4">
        <Logo />
        <nav aria-label="Main" className="mx-auto hidden items-center gap-1 lg:flex">
          {LINKS.map((l) => (
            <Link key={l.href} href={l.href} className="nav-link" aria-current={l.match(pathname) ? "page" : undefined}>{l.label}</Link>
          ))}
          <PagesMenu pathname={pathname} />
        </nav>
        <div className="ml-auto flex items-center gap-2 lg:ml-0">
          <StudentBadge />
          {signedOut ? (
            <>
              <Link href="/signin" className="btn btn-quiet !hidden !min-h-[38px] !px-4 lg:!inline-flex">Sign in</Link>
              <Link href="/signin" className="btn btn-primary !hidden !min-h-[38px] !px-4 lg:!inline-flex">Get started</Link>
            </>
          ) : null}
          <button
            type="button" aria-expanded={menu} aria-controls="mobile-nav" aria-label={menu ? "Close menu" : "Open menu"}
            onClick={() => setMenu((m) => !m)}
            className="grid size-11 place-items-center rounded-control border border-line text-ink lg:hidden"
          >
            <svg aria-hidden="true" width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              {menu ? <path d="M4 4l12 12M16 4L4 16" /> : <path d="M3 5h14M3 10h14M3 15h14" />}
            </svg>
          </button>
        </div>
      </div>
      <nav id="mobile-nav" aria-label="Mobile" hidden={!menu} className="border-t border-line bg-white lg:hidden">
        <div className="wrap flex flex-col py-3">
          {LINKS.map((l) => (
            <Link key={l.href} href={l.href} className="nav-link !py-3" aria-current={l.match(pathname) ? "page" : undefined}>{l.label}</Link>
          ))}
          {PAGES.map((p) => (
            <Link key={p.href} href={p.href} className="nav-link !py-3 !text-muted" aria-current={pathname.startsWith(p.href) ? "page" : undefined}>{p.label}</Link>
          ))}
          {signedOut ? (
            <div className="mt-2 flex gap-2">
              <Link href="/signin" className="btn btn-quiet flex-1">Sign in</Link>
              <Link href="/signin" className="btn btn-primary flex-1">Get started</Link>
            </div>
          ) : null}
        </div>
      </nav>
    </header>
  );
}
