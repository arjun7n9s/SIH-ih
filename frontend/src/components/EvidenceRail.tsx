import type { Source } from "../lib/types";

type Props = {
  sources: Source[];
  active: number | null;
  onPick: (n: number) => void;
};

export function EvidenceRail({ sources, active, onPick }: Props) {
  if (!sources.length) {
    return (
      <aside className="hidden lg:flex w-[320px] shrink-0 flex-col border-l-2 border-ink/15 p-5 text-ink/50">
        <p className="font-mono text-[10px] uppercase tracking-[0.18em]">Evidence</p>
        <p className="mt-6 text-sm leading-relaxed">
          Citations land here. Click [1] in the answer to open the chunk.
        </p>
      </aside>
    );
  }

  return (
    <aside className="hidden lg:flex w-[320px] shrink-0 flex-col border-l-2 border-ink overflow-y-auto">
      <p className="font-mono text-[10px] uppercase tracking-[0.18em] px-5 pt-5 pb-3 border-b-2 border-ink">
        Evidence · {sources.length}
      </p>
      <ul className="flex flex-col">
        {sources.map((s) => (
          <li key={s.n}>
            <button
              type="button"
              onClick={() => onPick(s.n)}
              className={`w-full text-left px-5 py-4 border-b-2 border-ink/10 ${
                active === s.n ? "bg-ink text-paper" : "hover:bg-ink/5"
              }`}
            >
              <span className="font-mono text-xs">[{s.n}]</span>
              <p className="mt-1 font-semibold text-sm leading-snug">{s.title}</p>
              {s.page != null && (
                <p className="mt-1 font-mono text-[10px] uppercase tracking-wider opacity-70">
                  p. {s.page}
                  {s.effective_from ? ` · from ${s.effective_from}` : ""}
                </p>
              )}
              <p className="mt-2 text-xs leading-relaxed opacity-80">{s.excerpt}</p>
            </button>
          </li>
        ))}
      </ul>
    </aside>
  );
}
