import { useEffect, useState, type ReactNode } from "react";
import { LOGO_SPRITE, ORG_HEADER_SRC, SITE_MIST } from "../lib/brand";
import { healthCheck } from "../lib/api";
import { LogoSprite } from "./LogoSprite";

type Props = {
  children: ReactNode;
  checkReady?: () => Promise<boolean>;
};

/**
 * Boot rule:
 * 1. Always play at least one full sprite loop (assemble → hold → unwind).
 * 2. If still not ready, keep looping until ready, then open.
 */
export function BootGate({ children, checkReady }: Props) {
  const [cycleDone, setCycleDone] = useState(false);
  const [ready, setReady] = useState(false);
  const [open, setOpen] = useState(false);
  const [status, setStatus] = useState("Opening Suchna");

  useEffect(() => {
    let cancelled = false;
    const img = new Image();
    img.src = LOGO_SPRITE.src;
    const org = new Image();
    org.src = ORG_HEADER_SRC;

    const cycleTimer = window.setTimeout(() => {
      if (!cancelled) setCycleDone(true);
    }, LOGO_SPRITE.durationMs);

    void (async () => {
      setStatus("Checking campus index");
      try {
        const ok = checkReady ? await checkReady() : Boolean(await healthCheck());
        if (cancelled) return;
        setReady(true);
        setStatus(ok ? "Index ready" : "Continuing offline");
      } catch {
        if (!cancelled) {
          setReady(true);
          setStatus("Continuing offline");
        }
      }
    })();

    return () => {
      cancelled = true;
      window.clearTimeout(cycleTimer);
    };
  }, [checkReady]);

  useEffect(() => {
    if (cycleDone && ready) {
      const t = window.setTimeout(() => setOpen(true), 100);
      return () => window.clearTimeout(t);
    }
  }, [cycleDone, ready]);

  if (!open) {
    return (
      <div
        className="fixed inset-0 z-[100] flex flex-col items-center justify-center gap-5 px-6"
        style={{ background: SITE_MIST }}
        role="status"
        aria-live="polite"
        aria-busy="true"
      >
        <LogoSprite size={112} label="Loading Suchna" />
        <img
          src={ORG_HEADER_SRC}
          alt="PDPM IIITDM Jabalpur"
          className="h-11 w-auto max-w-[min(90vw,320px)] object-contain sm:h-12"
        />
        <div className="text-center">
          <p className="text-sm font-semibold tracking-tight text-ink">Suchna</p>
          <p className="mt-1.5 font-mono text-[10px] uppercase tracking-[0.2em] text-muted">
            {cycleDone && !ready ? "Still loading campus docs" : status}
          </p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
