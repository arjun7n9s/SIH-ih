import { Mic, Paperclip } from "lucide-react";
import { useState, type FormEvent } from "react";

type Props = {
  disabled?: boolean;
  onSubmit: (query: string) => void;
  onUpload?: (file: File) => void;
};

export function Composer({ disabled, onSubmit, onUpload }: Props) {
  const [value, setValue] = useState("");

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const q = value.trim();
    if (!q) return;
    onSubmit(q);
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="border-t-2 border-ink bg-paper px-4 py-3 flex items-end gap-3"
    >
      <label className="shrink-0 pb-2 text-ink/70 hover:text-poster">
        <Paperclip size={18} />
        <input
          type="file"
          className="sr-only"
          accept="application/pdf,image/*"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) onUpload?.(file);
          }}
        />
      </label>
      <textarea
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSubmit(e);
          }
        }}
        rows={1}
        placeholder="Ask the ordinances, fees, hostels…"
        className="flex-1 resize-none bg-transparent border-0 border-b-2 border-ink py-2 text-[15px] outline-none placeholder:text-ink/40"
      />
      <button
        type="button"
        title="Speechmatics mic — paste SPEECHMATICS_API_KEY, Block E"
        className="shrink-0 pb-2 text-ink/70 hover:text-poster"
        onClick={() =>
          alert("Voice uses the official Speechmatics React SDK. Paste SPEECHMATICS_API_KEY in .env — not built yet.")
        }
      >
        <Mic size={18} />
      </button>
      <button type="submit" disabled={disabled} className="stamp px-4 py-2 text-sm">
        Ask →
      </button>
    </form>
  );
}
