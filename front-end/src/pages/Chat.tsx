import { History, Menu, X } from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { AnswerPanel } from "../components/AnswerPanel";
import { BootGate } from "../components/BootGate";
import { Composer } from "../components/Composer";
import { LogoLoader, LogoMark } from "../components/LogoMark";
import { OrgHeader } from "../components/OrgHeader";
import { VoiceOverlay } from "../components/VoiceOverlay";
import {
  SUGGESTIONS,
  healthCheck,
  runQuery,
  transcribeVoice,
  uploadCompanion,
} from "../lib/api";
import { statusLabelsFor } from "../lib/status";
import { emptyAnswer, type AnswerState, type ChatTurn } from "../lib/types";

function uid() {
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}

export function Chat() {
  return (
    <BootGate>
      <ChatShell />
    </BootGate>
  );
}

function ChatShell() {
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [banner, setBanner] = useState<string | null>(null);
  const [live, setLive] = useState<AnswerState | null>(null);
  const [history, setHistory] = useState<ChatTurn[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [sidebar, setSidebar] = useState(false);
  const [voiceOpen, setVoiceOpen] = useState(false);
  const [recording, setRecording] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [voiceError, setVoiceError] = useState<string | null>(null);
  const [readyLabel, setReadyLabel] = useState("Checking backend…");

  const mediaRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<BlobPart[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    void healthCheck().then((h) => {
      if (!h) {
        const local = import.meta.env.DEV;
        setReadyLabel(
          local
            ? "Campus index is offline"
            : "Campus index is unreachable",
        );
      } else if (h.live_chat) setReadyLabel("Campus index ready");
      else setReadyLabel("Answers available");
    });
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [live, history, busy]);

  const visible = useMemo(() => {
    if (activeId) return history.find((h) => h.id === activeId) ?? null;
    return null;
  }, [activeId, history]);

  const ask = useCallback(async (query: string) => {
    const q = query.trim();
    if (!q) return;
    setBusy(true);
    setBanner(null);
    setActiveId(null);
    setDraft("");
    const start = emptyAnswer(q);
    start.status = statusLabelsFor(q)[0];
    setLive(start);
    try {
      const final = await runQuery(q, setLive);
      const turn: ChatTurn = {
        id: uid(),
        query: q,
        answer: final,
        createdAt: Date.now(),
      };
      setHistory((prev) => [turn, ...prev].slice(0, 24));
      setActiveId(turn.id);
      setLive(null);
    } catch (err) {
      setBanner(err instanceof Error ? err.message : String(err));
      setLive(null);
    } finally {
      setBusy(false);
    }
  }, []);

  async function onUpload(file: File) {
    try {
      const json = await uploadCompanion(file);
      setBanner(json.banner || json.summary || "File attached for this session only.");
    } catch (err) {
      setBanner(err instanceof Error ? err.message : String(err));
    }
  }

  async function startVoice() {
    setVoiceError(null);
    setVoiceOpen(true);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];
      recorder.ondataavailable = (e) => {
        if (e.data.size) chunksRef.current.push(e.data);
      };
      recorder.onstop = () => {
        stream.getTracks().forEach((t) => t.stop());
        void finishVoice();
      };
      mediaRef.current = recorder;
      recorder.start();
      setRecording(true);
    } catch {
      setVoiceError("Microphone permission denied or unavailable.");
      setRecording(false);
    }
  }

  function stopVoice() {
    const rec = mediaRef.current;
    if (rec && rec.state !== "inactive") {
      setRecording(false);
      rec.stop();
    } else {
      setVoiceOpen(false);
    }
  }

  async function finishVoice() {
    setProcessing(true);
    setVoiceError(null);
    try {
      const blob = new Blob(chunksRef.current, { type: "audio/webm" });
      if (blob.size < 800) throw new Error("Clip too short — hold the mic a moment longer.");
      const result = await transcribeVoice(blob);
      if (!result.text?.trim()) throw new Error("Didn’t catch that — try speaking a little longer.");
      setDraft(result.text.trim());
      setVoiceOpen(false);
      setBanner("Transcript added — edit if needed, then send.");
    } catch (err) {
      setVoiceError(err instanceof Error ? err.message : String(err));
    } finally {
      setProcessing(false);
      mediaRef.current = null;
    }
  }

  const showing = live ?? visible?.answer ?? null;
  const empty = !showing && !busy;

  return (
    <div className="flex h-dvh overflow-hidden bg-mist">
      <aside
        className={`fixed inset-y-0 left-0 z-40 flex h-dvh w-[300px] flex-col border-r border-line bg-surface p-4 transition-transform lg:static lg:h-full lg:translate-x-0 ${
          sidebar ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="mb-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <History size={16} className="text-green" />
            <p className="text-sm font-semibold">Recent chats</p>
          </div>
          <button
            type="button"
            className="grid h-8 w-8 place-items-center rounded-full hover:bg-mist lg:hidden"
            onClick={() => setSidebar(false)}
          >
            <X size={16} />
          </button>
        </div>
        <button
          type="button"
          onClick={() => {
            setActiveId(null);
            setLive(null);
            setSidebar(false);
          }}
          className="mb-3 w-full rounded-2xl border border-dashed border-green/30 bg-green-soft/50 px-3 py-2.5 text-left text-sm font-medium text-green"
        >
          + New question
        </button>
        <div className="space-y-1 overflow-y-auto pb-8" style={{ maxHeight: "calc(100dvh - 140px)" }}>
          {history.length === 0 && (
            <p className="px-2 py-6 text-sm text-muted">Your questions will land here.</p>
          )}
          {history.map((h) => (
            <button
              key={h.id}
              type="button"
              onClick={() => {
                setActiveId(h.id);
                setLive(null);
                setSidebar(false);
              }}
              className={`w-full rounded-2xl px-3 py-2.5 text-left text-sm transition ${
                activeId === h.id ? "bg-green-soft text-ink" : "text-muted hover:bg-mist hover:text-ink"
              }`}
            >
              <span className="line-clamp-2 font-medium">{h.query}</span>
              <span className="mt-1 block font-mono text-[10px] uppercase tracking-wider opacity-70">
                {new Date(h.createdAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
              </span>
            </button>
          ))}
        </div>
      </aside>

      {sidebar && (
        <button
          type="button"
          aria-label="Close sidebar"
          className="fixed inset-0 z-30 bg-ink/20 lg:hidden"
          onClick={() => setSidebar(false)}
        />
      )}

      <div className="flex min-h-0 min-w-0 flex-1 flex-col">
        <header className="border-b-2 border-ink bg-paper/95 backdrop-blur">
          <div className="flex items-center justify-between gap-3 px-4 py-3">
            <div className="flex min-w-0 items-center gap-3">
              <button
                type="button"
                className="grid h-9 w-9 shrink-0 place-items-center border-2 border-ink bg-paper lg:hidden"
                onClick={() => setSidebar(true)}
                aria-label="Open recent chats"
              >
                <Menu size={16} />
              </button>
              <OrgHeader compact className="min-w-0" />
            </div>
            <div className="flex shrink-0 items-center gap-2">
              <div className="hidden text-right sm:block">
                <p className="text-sm font-semibold leading-none text-ink">Suchna</p>
                <p className="mt-1 font-mono text-[10px] uppercase tracking-[0.16em] text-muted">
                  {readyLabel}
                </p>
              </div>
              <Link
                to="/contradictions"
                className="border-2 border-ink px-3 py-1.5 font-mono text-[10px] uppercase tracking-[0.14em] hover:bg-ink hover:text-paper"
              >
                Contradictions
              </Link>
            </div>
          </div>
          <div className="suchna-tripwire" />
        </header>

        <div ref={scrollRef} className="min-h-0 flex-1 overflow-y-auto px-4 py-8 sm:px-8">
          <div className="mx-auto w-full max-w-2xl">
            {banner && (
              <p className="mb-4 rounded-2xl border border-blue/20 bg-blue-soft px-4 py-3 text-sm text-navy">
                {banner}
              </p>
            )}

            {empty ? (
              <div className="flex flex-col items-center pt-6 text-center sm:pt-10">
                <LogoMark size={96} label="Suchna" />
                <h1 className="mt-6 text-2xl font-semibold tracking-tight text-ink sm:text-3xl">
                  Hello, I’m Suchna
                </h1>
                <p className="mt-2 max-w-md text-sm leading-relaxed text-muted sm:text-base">
                  Your IIITDM Jabalpur knowledge partner — citations, dates, and
                  honest notes when two official PDFs disagree.
                </p>
                <div className="mt-8 grid w-full gap-2">
                  {SUGGESTIONS.map((s) => (
                    <button
                      key={s.query}
                      type="button"
                      disabled={busy}
                      onClick={() => void ask(s.query)}
                      className="card-lift flex items-center justify-between rounded-2xl border border-line bg-surface px-4 py-3 text-left text-sm"
                    >
                      <span className="font-medium text-ink">{s.label}</span>
                      <span className="text-muted">→</span>
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <>
                {busy && showing && !showing.text && (
                  <LogoLoader label={showing.status || "Searching campus docs…"} />
                )}
                {showing && (showing.text || showing.done) && <AnswerPanel answer={showing} />}
              </>
            )}
          </div>
        </div>

        <div className="border-t border-line bg-surface/90 px-4 py-4 backdrop-blur sm:px-8">
          <div className="mx-auto max-w-2xl">
            <Composer
              value={draft}
              disabled={busy}
              onChange={setDraft}
              onSubmit={() => void ask(draft)}
              onMic={() => void startVoice()}
              onUpload={(f) => void onUpload(f)}
            />
            <p className="mt-2 text-center font-mono text-[10px] uppercase tracking-[0.18em] text-muted">
              Enter to send · Mic for Hindi or Hinglish · + attaches a circular
            </p>
          </div>
        </div>
      </div>

      <VoiceOverlay
        open={voiceOpen}
        recording={recording}
        processing={processing}
        error={voiceError}
        onClose={() => {
          if (recording) stopVoice();
          else setVoiceOpen(false);
        }}
        onStop={stopVoice}
      />
    </div>
  );
}
