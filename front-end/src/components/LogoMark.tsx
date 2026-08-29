import { MARK_SRC } from "../lib/brand";

type Props = {
  size?: number;
  className?: string;
  label?: string;
};

/** Static campus mark — no sprite animation. */
export function LogoMark({ size = 88, className = "", label = "IIITDM Jabalpur" }: Props) {
  return (
    <img
      src={MARK_SRC}
      alt={label}
      width={size}
      height={size}
      className={`object-contain ${className}`}
      draggable={false}
    />
  );
}

export function LogoLoader({
  label = "Searching campus docs…",
  size = 72,
}: {
  label?: string;
  size?: number;
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-10">
      <LogoMark size={size} label={label} />
      <p className="max-w-xs text-center text-sm leading-relaxed text-muted">{label}</p>
    </div>
  );
}
