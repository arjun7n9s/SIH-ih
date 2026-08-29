import type { ChatEvent } from "../lib/types";

export function StructuredCard({
  card,
}: {
  card: Extract<ChatEvent, { type: "structure" }>;
}) {
  const keys = card.rows[0] ? Object.keys(card.rows[0]) : [];
  return (
    <section className="mt-6 border-2 border-ink bg-paper">
      <header className="flex items-center justify-between gap-3 px-4 py-2 border-b-2 border-ink bg-ink text-paper">
        <p className="font-mono text-[10px] uppercase tracking-[0.16em]">{card.kind}</p>
        <p className="text-sm font-semibold">{card.title}</p>
      </header>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b-2 border-ink">
              {keys.map((k) => (
                <th
                  key={k}
                  className="text-left font-mono text-[10px] uppercase tracking-wider px-4 py-2"
                >
                  {k}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {card.rows.map((row, i) => (
              <tr key={i} className="border-b border-ink/15">
                {keys.map((k) => (
                  <td key={k} className="px-4 py-2">
                    {row[k]}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
