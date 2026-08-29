import type { ChatEvent } from "../lib/types";

export function ContradictionCard({
  event,
}: {
  event: Extract<ChatEvent, { type: "contradiction" }>;
}) {
  return (
    <section className="mt-6 border-2 border-poster">
      <header className="px-4 py-2 bg-poster text-ink flex items-baseline justify-between gap-3">
        <p className="font-mono text-[10px] uppercase tracking-[0.16em]">Sources disagree</p>
        <p className="text-sm font-semibold">{event.claim}</p>
      </header>
      <div className="grid sm:grid-cols-2 divide-y sm:divide-y-0 sm:divide-x-2 divide-poster">
        {[event.a, event.b].map((side) => (
          <article key={side.n} className="p-4">
            <p className="font-mono text-xs">[{side.n}] {side.effective_from ?? "undated"}</p>
            <h3 className="mt-1 font-semibold text-sm leading-snug">{side.title}</h3>
            <p className="mt-2 text-sm leading-relaxed text-ink/80">{side.excerpt}</p>
            {side.page != null && (
              <p className="mt-2 font-mono text-[10px] uppercase tracking-wider">p. {side.page}</p>
            )}
          </article>
        ))}
      </div>
    </section>
  );
}
