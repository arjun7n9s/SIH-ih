import { useEffect, useState, type ReactNode } from "react";
import { MARK_SRC, SITE_MIST } from "../lib/brand";
import { healthCheck } from "../lib/api";
import { LogoMark } from "./LogoMark";

type Props = {
  children: ReactNode;
  checkReady?: () => Promise<boolean>;
};

/** Short static boot — campus mark only, no sprite / org lockup. */
export function BootGate({ children, checkReady }: Props) {
  const [open, setOpen] = useState(false);
  const [status, setStatus] = useState("Opening Suchna");

  useEffect(() => {
    let cancelled = false;
    const started = performance.now();
    const img = new Image();
    img.src = MARK_SRC;

    void (async () => {
      setStatus("Checking campus index");
      try {
        const ok = checkReady ? await checkReady() : Boolean(await healthCheck());
        if (cancelled) return;
        setStatus(ok ? "Index ready" : "Continuing offline");
      } catch {
        if (!cancelled) setStatus("Continuing offline");
      }
      const wait = Math.max(0, 450 - (performance.now() - started));
      window.setTimeout(() => {
        if (!cancelled) setOpen(true);
      }, wait);
    })();

    return () => {
      cancelled = true;
    };
  }, [checkReady]);

  if (!open) {
    return (
      <div
        className="fixed inset-0 z-[100] flex flex-col items-center justify-center gap-4 px-6"
        style={{ background: SITE_MIST }}
        role="status"
        aria-live="polite"
        aria-busy="true"
      >
        <LogoMark size={104} label="Loading Suchna" />
        <div className="text-center">
          <p className="text-sm font-semibold tracking-tight text-ink">Suchna</p>
          <p className="mt-1.5 font-mono text-[10px] uppercase tracking-[0.2em] text-muted">
            {status}
          </p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
