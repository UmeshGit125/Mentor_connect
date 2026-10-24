import { EmptyState } from "@/components/states";

export default function NotFound() {
  return <div className="page"><EmptyState title="We could not find that page" body="The link may be old or mistyped. Start from the chat or browse the mentor list." href="/mentors" cta="Browse mentors" /></div>;
}
