export function FreshnessBadge({
  asOf,
  lastUpdated,
}: {
  asOf: string;
  lastUpdated: string;
}) {
  return (
    <p className="inline-flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.16em] border-2 border-ink px-2 py-1">
      <span className="h-2 w-2 rounded-full bg-poster" />
      as of {asOf}
      <span className="opacity-50">doc {lastUpdated}</span>
    </p>
  );
}
