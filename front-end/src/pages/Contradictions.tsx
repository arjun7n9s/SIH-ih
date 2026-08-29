import { ArrowLeft, Scale } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchContradictions } from "../lib/api";
import type { Source } from "../lib/types";

type Item = { claim: string; a: Source; b: Source };

export function Contradictions() {
  const [items, setItems] = useState<Item[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void fetchContradictions()
      .then((res) => setItems(res.items ?? []))
      .catch((err) => setError(err instanceof Error ? err.message : String(err)));
  }, []);

  return (
    <div className="min-h-dvh bg-mist">
      <header className="border-b border-line bg-surface/90">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-5 py-4">
          <Link to="/app" className="inline-flex items-center gap-2 text-sm text-muted hover:text-ink">
            <ArrowLeft size={15} />
            Back to assistant
          </Link>
          <Link to="/" className="text-sm font-semibold text-ink">
            Suchna
          </Link>
        </div>
      </header>

      <main className="mx-auto max-w-3xl px-5 py-10">
        <div className="flex items-start gap-3">
          <span className="grid h-11 w-11 place-items-center rounded-2xl bg-warn-soft text-warn">
            <Scale size={20} />
          </span>
          <div>
            <p className="font-mono text-[10px] uppercase tracking-[0.22em] text-warn">
              Official sources
            </p>
            <h1 className="mt-1 text-3xl font-semibold tracking-tight text-ink">
              Where documents disagree
            </h1>
            <p className="mt-2 max-w-xl text-sm leading-relaxed text-muted">
              When two institute PDFs say different things, Suchna shows both instead of
              picking a quiet average.
            </p>
          </div>
        </div>

        {error && (
          <p className="mt-6 rounded-2xl border border-warn/30 bg-warn-soft px-4 py-3 text-sm text-warn">
            {error}
          </p>
        )}

        <div className="mt-8 space-y-4">
          {items.map((item, i) => (
            <article key={i} className="rounded-[24px] border border-line bg-surface p-5 shadow-sm">
              <p className="text-sm font-semibold text-ink">{item.claim}</p>
              <div className="mt-4 grid gap-3 sm:grid-cols-2">
                {[item.a, item.b].map((s) => (
                  <a
                    key={s.n + s.title}
                    href={s.url}
                    target="_blank"
                    rel="noreferrer"
                    className="rounded-2xl border border-line bg-mist/70 px-3 py-3 hover:border-green/35"
                  >
                    <p className="text-xs font-medium text-green">Source [{s.n}]</p>
                    <p className="mt-1 text-sm font-semibold text-ink">{s.title}</p>
                    <p className="mt-1 text-xs leading-relaxed text-muted">{s.excerpt}</p>
                  </a>
                ))}
              </div>
            </article>
          ))}
          {!error && items.length === 0 && (
            <p className="text-sm text-muted">Loading contradiction cards…</p>
          )}
        </div>
      </main>
    </div>
  );
}
