import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ContradictionCard } from "../components/ContradictionCard";
import { fetchContradictions } from "../lib/api";
import type { ChatEvent } from "../lib/types";

export function Contradictions() {
  const [items, setItems] = useState<Extract<ChatEvent, { type: "contradiction" }>[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchContradictions()
      .then((data) => {
        setItems(
          data.items.filter(
            (e): e is Extract<ChatEvent, { type: "contradiction" }> =>
              e.type === "contradiction",
          ),
        );
      })
      .catch((err: unknown) => setError(err instanceof Error ? err.message : String(err)));
  }, []);

  return (
    <div className="min-h-dvh flex flex-col">
      <header className="flex items-center justify-between px-5 py-3 border-b-2 border-ink">
        <Link to="/" className="text-lg font-semibold">
          Suchna
        </Link>
        <p className="font-mono text-[10px] uppercase tracking-[0.18em]">Contradictions</p>
      </header>
      <main className="max-w-3xl mx-auto w-full px-6 py-10">
        <h1 className="text-3xl font-semibold tracking-tight">Where the PDFs disagree</h1>
        <p className="mt-2 text-ink/70 max-w-xl">
          Seeded pairs from the IIITDMJ corpus. The bot does not silently pick a side.
        </p>
        {error && <p className="mt-6 text-poster">{error}</p>}
        <div className="mt-8 space-y-6">
          {items.map((event) => (
            <ContradictionCard key={event.claim} event={event} />
          ))}
        </div>
      </main>
    </div>
  );
}
