import { useCallback, useState } from "react";
import { Link } from "react-router-dom";
import { AnswerView } from "../components/AnswerView";
import { Composer } from "../components/Composer";
import { EvidenceRail } from "../components/EvidenceRail";
import { runQuery, SUGGESTIONS } from "../lib/api";
import { emptyAnswer, type AnswerState } from "../lib/types";

export function Home() {
  const [answer, setAnswer] = useState<AnswerState | null>(null);
  const [busy, setBusy] = useState(false);
  const [active, setActive] = useState<number | null>(null);
  const [banner, setBanner] = useState<string | null>(null);

  const ask = useCallback(async (query: string) => {
    setBusy(true);
    setActive(null);
    setBanner(null);
    setAnswer(emptyAnswer(query));
    try {
      await runQuery(query, setAnswer);
    } catch (err) {
      setBanner(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }, []);

  async function onUpload(file: File) {
    const body = new FormData();
    body.append("file", file);
    const res = await fetch("/api/companion", { method: "POST", body });
    const json = await res.json();
    setBanner(json.banner ?? "Upload received. Session is not saved.");
  }

  return (
    <div className="min-h-dvh flex flex-col">
      <header className="flex items-center justify-between px-5 py-3 border-b-2 border-ink">
        <div>
          <p className="font-mono text-[10px] uppercase tracking-[0.22em] text-poster">
            IIITDM Jabalpur
          </p>
          <Link to="/" className="text-lg font-semibold tracking-tight">
            Suchna
          </Link>
        </div>
        <nav className="flex items-center gap-4 font-mono text-[11px] uppercase tracking-wider">
          <Link to="/contradictions" className="hover:text-poster">
            Contradictions
          </Link>
          <span className="opacity-40">EN | HI</span>
        </nav>
      </header>

      <div className="flex flex-1 min-h-0">
        <main className="flex-1 overflow-y-auto px-6 py-10">
          {banner && (
            <p className="mb-6 border-2 border-poster px-3 py-2 text-sm">{banner}</p>
          )}
          {!answer ? (
            <div className="max-w-xl mt-16">
              <p className="font-mono text-[10px] uppercase tracking-[0.22em] text-poster">
                College knowledge assistant
              </p>
              <h1 className="mt-3 text-4xl font-semibold tracking-tight leading-[1.05]">
                Ask the institute.
                <br />
                Get the page.
              </h1>
              <p className="mt-4 text-ink/70 leading-relaxed max-w-md">
                Citations open the chunk. When two PDFs disagree, both stay on screen.
              </p>
              <div className="mt-8 flex flex-wrap gap-2">
                {SUGGESTIONS.map((s) => (
                  <button
                    key={s.query}
                    type="button"
                    className="chip"
                    onClick={() => void ask(s.query)}
                  >
                    {s.label}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <AnswerView answer={answer} onCite={setActive} />
          )}
        </main>
        <EvidenceRail
          sources={answer?.sources ?? []}
          active={active}
          onPick={setActive}
        />
      </div>
      <Composer disabled={busy} onSubmit={(q) => void ask(q)} onUpload={(f) => void onUpload(f)} />
    </div>
  );
}
