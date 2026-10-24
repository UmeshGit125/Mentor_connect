import Link from "next/link";

export function EmptyState({ title, body, href, cta }: { title: string; body: string; href?: string; cta?: string }) {
  return (
    <div data-testid="empty-state" className="rounded-card border border-dashed border-[#c6cfce] bg-wash p-6 md:p-8">
      <h2 className="text-xl">{title}</h2>
      <p className="mt-2 measure text-muted">{body}</p>
      {href && cta ? (
        <Link href={href} className="btn btn-primary mt-4">{cta}</Link>
      ) : null}
    </div>
  );
}

export function ErrorState({ title = "That did not load", message, onRetry }: { title?: string; message: string; onRetry?: () => void }) {
  return (
    <div role="alert" data-testid="error-state" className="rounded-card border border-danger/40 bg-danger-wash p-6">
      <h2 className="text-xl text-danger">{title}</h2>
      <p className="mt-2 measure">{message}</p>
      {onRetry ? (
        <button type="button" onClick={onRetry} className="btn btn-quiet mt-4">Try again</button>
      ) : null}
    </div>
  );
}

export function Loading({ rows = 3, label = "Loading" }: { rows?: number; label?: string }) {
  return (
    <div role="status" aria-live="polite" data-testid="loading" className="space-y-3">
      <span className="sr-only">{label}</span>
      {Array.from({ length: rows }, (_, i) => (
        <div key={i} className="skeleton h-24 w-full" />
      ))}
    </div>
  );
}
