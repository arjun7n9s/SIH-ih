import { useMemo } from "react";
import type { ReactNode } from "react";
import type { AnswerState } from "../lib/types";
import { ContradictionCard } from "./ContradictionCard";
import { FreshnessBadge } from "./FreshnessBadge";
import { StructuredCard } from "./StructuredCard";

function renderBody(text: string, onCite: (n: number) => void): ReactNode[] {
  const nodes: ReactNode[] = [];
  const re = /(\*\*[^*]+\*\*|\[\d+\])/g;
  let last = 0;
  let key = 0;
  for (const match of text.matchAll(re)) {
    const i = match.index ?? 0;
    if (i > last) nodes.push(<span key={key++}>{text.slice(last, i)}</span>);
    const token = match[0];
    if (token.startsWith("**")) {
      nodes.push(<strong key={key++}>{token.slice(2, -2)}</strong>);
    } else {
      const n = Number(token.slice(1, -1));
      nodes.push(
        <button
          key={key++}
          type="button"
          onClick={() => onCite(n)}
          className="inline-flex translate-y-[-1px] mx-0.5 px-1 font-mono text-[11px] border-2 border-ink bg-paper hover:bg-ink hover:text-paper"
        >
          {token}
        </button>,
      );
    }
    last = i + token.length;
  }
  if (last < text.length) nodes.push(<span key={key++}>{text.slice(last)}</span>);
  return nodes;
}

export function AnswerView({
  answer,
  onCite,
}: {
  answer: AnswerState;
  onCite: (n: number) => void;
}) {
  const body = useMemo(
    () => renderBody(answer.text, onCite),
    [answer.text, onCite],
  );

  return (
    <article className="max-w-2xl">
      <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-ink/60">
        Query
      </p>
      <h1 className="mt-1 text-2xl font-semibold leading-tight">{answer.query}</h1>
      {answer.freshness && (
        <div className="mt-3">
          <FreshnessBadge
            asOf={answer.freshness.asOf}
            lastUpdated={answer.freshness.lastUpdated}
          />
        </div>
      )}
      {answer.status && (
        <p className="mt-6 font-mono text-xs uppercase tracking-wider text-poster">
          {answer.status}
        </p>
      )}
      {answer.text && (
        <p className="mt-6 text-[17px] leading-[1.55] whitespace-pre-wrap">{body}</p>
      )}
      {answer.structure && <StructuredCard card={answer.structure} />}
      {answer.contradiction && <ContradictionCard event={answer.contradiction} />}
    </article>
  );
}
