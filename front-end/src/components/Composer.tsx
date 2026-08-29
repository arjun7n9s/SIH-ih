import { Mic, Plus, SendHorizontal } from "lucide-react";
import { useRef, useState } from "react";

type Props = {
  value: string;
  disabled?: boolean;
  placeholder?: string;
  onChange: (v: string) => void;
  onSubmit: () => void;
  onMic: () => void;
  onUpload: (file: File) => void;
};

export function Composer({
  value,
  disabled,
  placeholder = "Ask about fees, attendance, hostels…",
  onChange,
  onSubmit,
  onMic,
  onUpload,
}: Props) {
  const fileRef = useRef<HTMLInputElement>(null);
  const [focused, setFocused] = useState(false);

  return (
    <div
      className={`rounded-[28px] border bg-surface px-3 py-2.5 shadow-[0_18px_50px_-32px_rgba(10,47,107,0.35)] transition ${
        focused ? "border-green/40 ring-4 ring-green-soft" : "border-line"
      }`}
    >
      <div className="flex items-end gap-2">
        <button
          type="button"
          aria-label="Attach a circular"
          disabled={disabled}
          onClick={() => fileRef.current?.click()}
          className="mb-0.5 grid h-10 w-10 shrink-0 place-items-center rounded-full text-muted hover:bg-mist hover:text-ink disabled:opacity-40"
        >
          <Plus size={18} />
        </button>
        <input
          ref={fileRef}
          type="file"
          className="hidden"
          accept=".pdf,.png,.jpg,.jpeg,.txt,.md"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) onUpload(f);
            e.currentTarget.value = "";
          }}
        />

        <textarea
          rows={1}
          value={value}
          disabled={disabled}
          placeholder={placeholder}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          onChange={(e) => {
            onChange(e.target.value);
            e.currentTarget.style.height = "auto";
            e.currentTarget.style.height = `${Math.min(e.currentTarget.scrollHeight, 140)}px`;
          }}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              if (!disabled && value.trim()) onSubmit();
            }
          }}
          className="max-h-36 min-h-10 flex-1 resize-none bg-transparent py-2.5 text-[15px] leading-relaxed text-ink outline-none placeholder:text-muted/80 disabled:opacity-50"
        />

        <button
          type="button"
          aria-label="Voice input"
          disabled={disabled}
          onClick={onMic}
          className="mb-0.5 grid h-10 w-10 shrink-0 place-items-center rounded-full text-muted hover:bg-blue-soft hover:text-blue disabled:opacity-40"
        >
          <Mic size={18} />
        </button>
        <button
          type="button"
          aria-label="Send"
          disabled={disabled || !value.trim()}
          onClick={onSubmit}
          className="mb-0.5 grid h-10 w-10 shrink-0 place-items-center rounded-full bg-ink text-paper shadow-[3px_3px_0_var(--color-poster)] disabled:opacity-35"
        >
          <SendHorizontal size={16} />
        </button>
      </div>
    </div>
  );
}
