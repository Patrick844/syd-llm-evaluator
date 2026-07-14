import type { ReactNode } from "react";
import type { ChatMessage } from "../types";
import Sources from "./Sources";

/** Highlights inline citations like [PH001 - CDC] and **bold**. */
function render(text: string): ReactNode[] {
  const parts: ReactNode[] = [];
  const regex = /(\[[^\]]+\]|\*\*[^*]+\*\*)/g;
  let last = 0;
  let m: RegExpExecArray | null;
  let key = 0;
  while ((m = regex.exec(text)) !== null) {
    if (m.index > last) parts.push(text.slice(last, m.index));
    const tok = m[0];
    if (tok.startsWith("**")) {
      parts.push(<strong key={key++}>{tok.slice(2, -2)}</strong>);
    } else {
      parts.push(
        <span key={key++} className="text-emerald-600 font-medium">
          {tok}
        </span>
      );
    }
    last = m.index + tok.length;
  }
  if (last < text.length) parts.push(text.slice(last));
  return parts;
}

export default function Message({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed whitespace-pre-wrap ${
          isUser ? "bg-emerald-600 text-white" : "bg-white border border-slate-200 text-slate-800"
        }`}
      >
        {render(message.content)}
        {!isUser && message.safety?.checked && (
          <div className="mt-2">
            {message.safety.blocked ? (
              <span className="inline-flex items-center gap-1 text-[11px] font-medium text-amber-700 bg-amber-50 border border-amber-200 rounded-full px-2 py-0.5">
                ⚠ Blocked by safety check
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-full px-2 py-0.5">
                ✓ Grounded &amp; safety-checked
              </span>
            )}
          </div>
        )}
        {!isUser && message.sources && <Sources sources={message.sources} />}
      </div>
    </div>
  );
}
