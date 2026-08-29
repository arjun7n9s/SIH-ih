import { AlertTriangle, ExternalLink } from "lucide-react";
import type { AnswerState } from "../lib/types";

function cleanExcerpt(text: string) {
  return text
    .replace(/<[^>]+>/g, " ")
    .replace(/&nbsp;/g, " ")
    .replace(/&amp;/g, "&")
    .replace(/&quot;/g, '"')
    .replace(/\s+/g, " ")
    .trim();
}

export function AnswerPanel({ answer }: { answer: AnswerState }) {
  return (
    <div className="space-y-4">
      <div className="rounded-[24px] border border-line bg-surface p-5 shadow-sm">
        <p className="text-xs font-medium uppercase tracking-[0.16em] text-muted">You</p>
        <p className="mt-2 text-[15px] leading-relaxed text-ink">{answer.query}</p>
      </div>

      <div className="rounded-[24px] border border-line bg-surface p-5 shadow-sm">
        <div className="flex flex-wrap items-center gap-2">
          <p className="text-xs font-medium uppercase tracking-[0.16em] text-green">Suchna</p>
          {answer.freshness && (
            <span className="rounded-full bg-blue-soft px-2.5 py-0.5 font-mono text-[10px] uppercase tracking-wider text-blue">
              as of {answer.freshness.asOf || answer.freshness.lastUpdated}
            </span>
          )}
          {answer.status && (
            <span className="rounded-full bg-mist px-2.5 py-0.5 text-[11px] text-muted">
              {answer.status}
            </span>
          )}
        </div>

        <div className="mt-3 whitespace-pre-wrap text-[15px] leading-7 text-ink">
          {answer.text || (answer.done ? "No answer returned." : "…")}
        </div>

        {answer.structure && (
          <div className="mt-5 overflow-hidden rounded-2xl border border-line">
            <div className="border-b border-line bg-mist px-3 py-2 text-sm font-medium">
              {answer.structure.title}
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full text-left text-sm">
                <thead className="bg-green-soft/50 text-muted">
                  <tr>
                    {Object.keys(answer.structure.rows[0] ?? {}).map((k) => (
                      <th key={k} className="px-3 py-2 font-medium">
                        {k}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {answer.structure.rows.map((row, i) => (
                    <tr key={i} className="border-t border-line">
                      {Object.values(row).map((v, j) => (
                        <td key={j} className="px-3 py-2 align-top text-ink/90">
                          {v}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {answer.contradiction && (
          <div className="mt-5 rounded-2xl border border-warn/30 bg-warn-soft p-4">
            <div className="flex items-center gap-2 text-warn">
              <AlertTriangle size={16} />
              <p className="text-sm font-semibold">Sources disagree</p>
            </div>
            <p className="mt-2 text-sm leading-relaxed text-ink/90">
              {answer.contradiction.claim}
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              {[answer.contradiction.a, answer.contradiction.b].map((s) => (
                <a
                  key={s.n}
                  href={s.url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex max-w-full items-center gap-1.5 rounded-full border border-warn/25 bg-surface px-3 py-1.5 text-xs font-medium text-ink hover:border-warn/50"
                >
                  <span className="text-warn">[{s.n}]</span>
                  <span className="truncate">{s.title}</span>
                </a>
              ))}
            </div>
          </div>
        )}

        {answer.sources.length > 0 && (
          <div className="mt-5">
            <p className="text-xs font-medium uppercase tracking-[0.16em] text-muted">
              Sources
            </p>
            <div className="mt-2 flex flex-wrap gap-2">
              {answer.sources.map((s) => {
                const tip = cleanExcerpt(s.excerpt);
                const page = s.page != null ? ` · p.${s.page}` : "";
                return (
                  <a
                    key={`${s.n}-${s.url}`}
                    href={s.url}
                    target="_blank"
                    rel="noreferrer"
                    title={tip}
                    className="group inline-flex max-w-full items-center gap-1.5 rounded-full border border-line bg-mist/70 px-3 py-1.5 text-xs text-ink hover:border-green/40 hover:bg-green-soft/50"
                  >
                    <span className="grid h-5 w-5 shrink-0 place-items-center rounded-full bg-green text-[10px] font-semibold text-white">
                      {s.n}
                    </span>
                    <span className="truncate font-medium">
                      {s.title}
                      {page}
                    </span>
                    <ExternalLink
                      size={12}
                      className="shrink-0 opacity-40 group-hover:opacity-70"
                    />
                  </a>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
