import { applyEvent } from "./reduce";
import { emptyAnswer, type AnswerState, type ChatEvent } from "./types";

const API = import.meta.env.VITE_API_URL || "";

export const SUGGESTIONS = [
  { label: "Attendance policy", query: "What is the attendance policy?" },
  { label: "वापसी का नियम?", query: "वापसी का नियम क्या है?" },
  { label: "Hostel fee", query: "What is the hostel fee?" },
  { label: "Rule in 2023", query: "What was the rule in 2023?" },
];

export async function* streamChat(query: string): AsyncGenerator<ChatEvent> {
  const res = await fetch(`${API}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
  });
  if (!res.ok || !res.body) {
    throw new Error(`chat failed ${res.status}`);
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

export async function fetchContradictions(): Promise<{ items: ChatEvent[] }> {
  const res = await fetch(`${API}/api/contradictions`);
  if (!res.ok) throw new Error("contradictions failed");
  return res.json();
}

export async function runQuery(
  query: string,
  onTick: (s: AnswerState) => void,
): Promise<void> {
  let state = emptyAnswer(query);
  onTick(state);
  for await (const event of streamChat(query)) {
    state = applyEvent(state, event);
    onTick({ ...state });
  }
}
