import {
  CalendarClock,
  FileSearch,
  Languages,
  Scale,
  Table2,
  Upload,
  type LucideIcon,
} from "lucide-react";

const MAP: Record<string, LucideIcon> = {
  languages: Languages,
  "file-search": FileSearch,
  scale: Scale,
  table: Table2,
  calendar: CalendarClock,
  upload: Upload,
};

export function FeatureIcon({ name }: { name: string }) {
  const Icon = MAP[name] ?? FileSearch;
  return (
    <span className="grid h-10 w-10 place-items-center border-2 border-ink bg-green-soft text-poster">
      <Icon size={18} strokeWidth={2.2} />
    </span>
  );
}
