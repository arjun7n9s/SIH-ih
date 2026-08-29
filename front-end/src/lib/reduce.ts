import type { AnswerState, ChatEvent } from "./types";

export function applyEvent(state: AnswerState, event: ChatEvent): AnswerState {
  switch (event.type) {
    case "status":
      return { ...state, status: event.label };
    case "token":
      return { ...state, text: state.text + event.text, status: "" };
    case "sources":
      return { ...state, sources: event.items };
    case "structure":
      return { ...state, structure: event };
    case "contradiction":
      return { ...state, contradiction: event };
    case "freshness":
      return { ...state, freshness: event };
    case "done":
      return { ...state, done: true, status: "" };
    default:
      return state;
  }
}
