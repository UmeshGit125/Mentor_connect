export function Legal({ title, updated, sections }: { title: string; updated: string; sections: { h: string; p: string[] }[] }) {
  return (
    <div className="page">
      <article className="mx-auto max-w-[760px]">
        <h1 className="h-page md:!text-[2.25rem]">{title}</h1>
        <p className="mt-2 text-sm text-muted">Last updated {updated}</p>
        <p className="mt-6 rounded-card border border-brand/40 bg-mint p-4 text-[0.95rem]">
          Mentor Connect is a prototype. This page is a plain-language placeholder and not legal advice. It will be replaced before any public launch.
        </p>
        {sections.map((s) => (
          <section key={s.h} className="mt-9">
            <h2 className="text-xl">{s.h}</h2>
            {s.p.map((t) => <p key={t} className="mt-3 leading-7 text-muted">{t}</p>)}
          </section>
        ))}
      </article>
    </div>
  );
}
