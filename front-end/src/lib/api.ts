import { applyEvent } from "./reduce";
import {
  emptyAnswer,
  type AnswerState,
  type ChatEvent,
  type HistoryTurn,
  type Source,
} from "./types";

const API = import.meta.env.VITE_API_URL || "";

export const SUGGESTIONS = [
  { label: "Attendance policy", query: "What is the attendance policy?" },
  { label: "Hostel fee", query: "What is the hostel fee for 2025?" },
  { label: "वापसी का नियम?", query: "वापसी का नियम क्या है?" },
  { label: "Rule in 2023", query: "What was the fee rule in 2023?" },
  { label: "Refund window", query: "What is the refund window after admission?" },
];

export const FEATURES = [
  {
    title: "Ask in English or Hinglish",
    body: "Type or speak campus questions the way students actually talk. Voice works in Hindi, English, and Hinglish; answers stay grounded in institute docs.",
    icon: "languages" as const,
  },
  {
    title: "Citations, not vibes",
    body: "Every answer points back to the ordinance, fee circular, or guideline page so you can open the source yourself.",
    icon: "file-search" as const,
  },
  {
    title: "Contradiction radar",
    body: "When two official PDFs disagree, Suchna keeps both on screen instead of picking a quiet average.",
    icon: "scale" as const,
  },
  {
    title: "Tables when fees matter",
    body: "Fee and refund structures surface as readable tables pulled from the corpus, not a wall of prose.",
    icon: "table" as const,
  },
  {
    title: "Freshness badges",
    body: "See the as-of date on answers so a 2017 guideline never quietly pretends to be this semester.",
    icon: "calendar" as const,
  },
  {
    title: "Attach a circular",
    body: "Drop a handout for a short, one-session summary while you keep asking the live campus index.",
    icon: "upload" as const,
  },
];

export async function* streamChat(
  query: string,
  history: HistoryTurn[] = [],
): AsyncGenerator<ChatEvent> {
  const res = await fetch(`${API}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, history }),
  });
  if (!res.ok || !res.body) {
    let detail = "";
    try {
      detail = (await res.text()).slice(0, 180);
    } catch {
      /* ignore */
    }
    const where = API || "same-origin /api";
    throw new Error(
      `Chat failed (${res.status}) via ${where}.${detail ? ` ${detail}` : " Backend may still be starting — retry."}`,
    );
  }
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buf = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    const parts = buf.split("\n\n");
    buf = parts.pop() ?? "";
    for (const part of parts) {
      const line = part.split("\n").find((l) => l.startsWith("data: "));
      if (!line) continue;
      yield JSON.parse(line.slice(6)) as ChatEvent;
    }
  }
}

export async function runQuery(
  query: string,
  onTick: (s: AnswerState) => void,
  history: HistoryTurn[] = [],
): Promise<AnswerState> {
  let state = emptyAnswer(query);
  onTick(state);
  for await (const event of streamChat(query, history)) {
    state = applyEvent(state, event);
    onTick({ ...state });
  }
  return state;
}

export async function fetchContradictions(): Promise<{
  items: Array<{ claim: string; a: Source; b: Source }>;
}> {
  const res = await fetch(`${API}/api/contradictions`);
  if (!res.ok) throw new Error("Could not load contradictions");
  return res.json();
}

export async function transcribeVoice(blob: Blob, filename = "voice.webm") {
  const body = new FormData();
  body.append("file", blob, filename);
  const res = await fetch(`${API}/api/voice/batch`, { method: "POST", body });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || `Voice failed (${res.status})`);
  }
  return res.json() as Promise<{ text: string; languages?: string[]; model?: string }>;
}

export async function uploadCompanion(file: File) {
  const body = new FormData();
  body.append("file", file);
  const res = await fetch(`${API}/api/companion`, { method: "POST", body });
  if (!res.ok) throw new Error(`Upload failed (${res.status})`);
  return res.json() as Promise<{ banner?: string; summary?: string; id?: string }>;
}

export async function healthCheck() {
  try {
    const res = await fetch(`${API}/health`);
    if (!res.ok) return null;
    return res.json() as Promise<{
      ok: boolean;
      live_chat?: boolean;
      unlocker?: boolean;
      speechmatics?: boolean;
    }>;
  } catch {
    return null;
  }
}
