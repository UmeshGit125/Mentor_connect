"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Logo } from "@/components/logo";

const SERVICES = [
  { href: "/mentors", label: "Mentors" },
  { href: "/faqs", label: "FAQs" },
  { href: "/sessions", label: "Sessions" },
  { href: "/contact", label: "Contact" },
];
const PAGES = [
  { href: "/terms", label: "Terms and Condition" },
  { href: "/privacy", label: "Privacy Policy" },
];

function Group({ title, links }: { title: string; links: { href: string; label: string }[] }) {
  return (
    <nav aria-label={title}>
      <h2 className="text-[1.05rem] font-semibold">{title}</h2>
      <ul className="mt-5 space-y-2.5">
        {links.map((l) => (
          <li key={l.href}>
            <Link href={l.href} className="text-[0.95rem] text-muted transition-colors hover:text-signal">{l.label}</Link>
          </li>
        ))}
      </ul>
    </nav>
  );
}

export function SiteFooter() {
  if (usePathname().startsWith("/admin")) return null;
  return (
    <footer className="mt-auto border-t border-line bg-white">
      <div className="wrap grid gap-10 py-14 md:grid-cols-[1fr_auto_auto] md:gap-24">
        <div>
          <Logo />
          <p className="mt-5 max-w-sm font-medium">Helping students find the right mentor and book a call.</p>
        </div>
        <Group title="Services" links={SERVICES} />
        <Group title="Pages" links={PAGES} />
      </div>
      <div className="border-t border-line py-6 text-center text-[0.95rem] font-medium">© 2026 Mentor Connect. A prototype. All rights reserved.</div>
    </footer>
  );
}
