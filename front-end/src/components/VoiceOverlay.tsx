import { Loader2, Mic, Square, X } from "lucide-react";

type Props = {
  open: boolean;
  recording: boolean;
  processing: boolean;
  error: string | null;
  onClose: () => void;
  onStop: () => void;
};

export function VoiceOverlay({
  open,
  recording,
  processing,
  error,
  onClose,
  onStop,
}: Props) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 grid place-items-end bg-ink/25 p-4 backdrop-blur-[2px] sm:place-items-center">
      <div className="w-full max-w-md rounded-[28px] border border-line bg-surface p-6 shadow-2xl">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="font-mono text-[10px] uppercase tracking-[0.22em] text-green">
              Melia multilingual
            </p>
            <h2 className="mt-1 text-lg font-semibold text-ink">
              {processing ? "Transcribing…" : recording ? "Listening…" : "Voice"}
            </h2>
            <p className="mt-1 text-sm text-muted">
              Speak in English, Hindi, or Hinglish. Audio goes to Melia-1 batch, then
              into your question box.
            </p>
          </div>
          <button
            type="button"
            aria-label="Close voice"
            onClick={onClose}
            className="grid h-9 w-9 place-items-center rounded-full border border-line text-muted hover:bg-mist"
          >
            <X size={16} />
          </button>
        </div>

        <div className="mt-8 flex flex-col items-center gap-5">
          <div className="flex h-10 items-end gap-1">
            {Array.from({ length: 18 }).map((_, i) => (
              <span
                key={i}
                className={`wave-bar w-1 rounded-full bg-gradient-to-t from-green to-blue-bright ${
                  recording || processing ? "" : "opacity-30"
                }`}
                style={{
                  height: `${10 + ((i * 7) % 22)}px`,
                  animationDelay: `${i * 45}ms`,
                }}
              />
            ))}
          </div>

          {error && (
            <p className="rounded-2xl border border-warn/30 bg-warn-soft px-3 py-2 text-center text-sm text-warn">
              {error}
            </p>
          )}

          <button
            type="button"
            onClick={processing ? undefined : onStop}
            disabled={processing}
            className="grid h-16 w-16 place-items-center rounded-full bg-gradient-to-br from-green to-blue text-white shadow-[0_16px_40px_-18px_rgba(11,122,59,0.8)] disabled:opacity-70"
          >
            {processing ? (
              <Loader2 className="animate-spin" size={22} />
            ) : recording ? (
              <Square size={18} fill="currentColor" />
            ) : (
              <Mic size={22} />
            )}
          </button>
          <p className="text-xs text-muted">
            {processing ? "Sending clip to Melia…" : "Tap to stop and fill the composer"}
          </p>
        </div>
      </div>
    </div>
  );
}
