export type Source = {
  n: number;
  title: string;
  url: string;
  page: number | null;
  excerpt: string;
  effective_from?: string | null;
  last_updated?: string | null;
};

export type ChatEvent =
  | { type: "status"; label: string }
  | { type: "token"; text: string }
  | { type: "sources"; items: Source[] }
  | {
      type: "structure";
      kind: string;
      title: string;
      rows: Record<string, string>[];
    }
  | { type: "contradiction"; claim: string; a: Source; b: Source }
  | { type: "freshness"; asOf: string; lastUpdated: string }
  | { type: "done" };

export type AnswerState = {
  query: string;
  status: string;
  text: string;
  sources: Source[];
  structure: Extract<ChatEvent, { type: "structure" }> | null;
  contradiction: Extract<ChatEvent, { type: "contradiction" }> | null;
  freshness: Extract<ChatEvent, { type: "freshness" }> | null;
  done: boolean;
};

export const emptyAnswer = (query = ""): AnswerState => ({
  query,
  status: "",
  text: "",
  sources: [],
  structure: null,
  contradiction: null,
  freshness: null,
  done: false,
});
