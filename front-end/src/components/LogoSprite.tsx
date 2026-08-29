import { useEffect, useRef } from "react";
import { LOGO_SPRITE } from "../lib/brand";

type Size = "sm" | "md" | "lg" | "xl";

const SIZES: Record<Size, number> = {
  sm: 40,
  md: 64,
  lg: 88,
  xl: 112,
};

type Props = {
  size?: Size | number;
  label?: string;
  className?: string;
  /** Pause on frame 0 */
  paused?: boolean;
};

/**
 * Plays the user 8×4 assemble/disassemble sprite (row-major, 32 frames).
 * Uses rAF so the 2D grid advances smoothly — not a 1D CSS steps hack.
 */
export function LogoSprite({
  size = "lg",
  label = "Loading",
  className = "",
  paused = false,
}: Props) {
  const ref = useRef<HTMLSpanElement>(null);
  const px = typeof size === "number" ? size : SIZES[size];

  useEffect(() => {
    const el = ref.current;
    if (!el || paused) {
      if (el) el.style.backgroundPosition = "0 0";
      return;
    }

    const { cols, frames, fps } = LOGO_SPRITE;
    const frameMs = 1000 / fps;
    let frame = 0;
    let raf = 0;
    let last = performance.now();
    let acc = 0;

    const paint = (f: number) => {
      const col = f % cols;
      const row = Math.floor(f / cols);
      // background-size is (cols*px) × (rows*px); position shifts by cell
      el.style.backgroundPosition = `-${col * px}px -${row * px}px`;
    };

    paint(0);

    const tick = (now: number) => {
      acc += now - last;
      last = now;
      while (acc >= frameMs) {
        acc -= frameMs;
        frame = (frame + 1) % frames;
        paint(frame);
      }
      raf = requestAnimationFrame(tick);
    };

    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [px, paused]);

  return (
    <span
      ref={ref}
      role="img"
      aria-label={label}
      className={`logo-sprite inline-block shrink-0 ${className}`}
      style={{
        width: px,
        height: px,
        backgroundImage: `url(${LOGO_SPRITE.src})`,
        backgroundRepeat: "no-repeat",
        backgroundSize: `${LOGO_SPRITE.cols * px}px ${LOGO_SPRITE.rows * px}px`,
        backgroundPosition: "0 0",
      }}
    />
  );
}

export function LogoLoader({
  label = "Searching campus docs…",
  size = "lg",
}: {
  label?: string;
  size?: Size | number;
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-10">
      <LogoSprite size={size} label={label} />
      <p className="font-mono text-[10px] uppercase tracking-[0.22em] text-muted">{label}</p>
    </div>
  );
}
