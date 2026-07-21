import { useEffect, useRef, useState } from "react";
import { ask, ApiError } from "./api";
import type { ChatMessage } from "./types";
import Message from "./components/Message";
import { track } from "./analytics";

// Phrased to map onto real knowledge-base entries so the demo returns a good match:
// flu → PH001, sleep → PH010, blood pressure → PH006, colorectal → PH003, tobacco → PH007.
const EXAMPLES = [
  "Do I need a flu shot?",
  "How much sleep do adults need?",
  "Who should get their blood pressure checked?",
  "When should I start colorectal cancer screening?",
  "How can I quit smoking?",
];

function Dots() {
  return (
    <div className="flex gap-1 items-center">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"
          style={{ animationDelay: `${i * 0.15}s` }}
        />
      ))}
    </div>
  );
}

export default function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length, loading]);

  const submit = async (question: string) => {
    const q = question.trim();
    if (!q || loading) return;
    const history = messages;
    setMessages((m) => [...m, { role: "user", content: q }]);
    setInput("");
    setError("");
    setLoading(true);
    try {
      const res = await ask(q, history);
      setMessages((m) => [
        ...m,
        { role: "assistant", content: res.answer, sources: res.sources, safety: res.safety },
      ]);
      // Usage signal — metadata only, never the question text (health privacy).
      // This is the only place SYD's guardrail outcomes are recorded anywhere.
      const scores = (res.sources ?? []).map((s) => s.score ?? 0);
      track("syd_question_asked", {
        turn: history.length / 2 + 1,
        question_length: q.length,
        blocked: res.safety?.blocked ?? false,
        groundedness: res.safety?.groundedness ?? null,
        medical_safety: res.safety?.medical_safety ?? null,
        num_sources: res.sources?.length ?? 0,
        top_score: scores.length ? Math.max(...scores) : 0,
      });
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Something went wrong.");
      track("syd_ask_failed", { reason: e instanceof ApiError ? e.message : "unknown" });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-dvh flex flex-col bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto max-w-3xl px-4 py-3 flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-emerald-600 text-white flex items-center justify-center text-lg">
            ⚕️
          </div>
          <div>
            <h1 className="font-semibold text-slate-900 leading-tight">SYD — Preventive Health Assistant</h1>
            <p className="text-xs text-slate-500">Answers grounded in referenced guidelines — with sources</p>
          </div>
        </div>
        <div className="border-t border-amber-100 bg-amber-50">
          <div className="mx-auto max-w-3xl px-4 py-2 flex items-start gap-2 text-[11px] leading-snug text-amber-800">
            <span aria-hidden className="mt-px">ⓘ</span>
            <p>
              <span className="font-semibold">Grounded in trusted sources.</span>{" "}
              SYD answers from CDC/USPSTF preventive-health guidance and cites every source. The
              knowledge base is actively expanding, so coverage keeps growing. Informational only
              — not medical advice.
            </p>
          </div>
        </div>
      </header>

      <main className="flex-1 mx-auto w-full max-w-3xl px-4 py-6 flex flex-col">
        {messages.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center text-center gap-5">
            <div className="w-14 h-14 rounded-2xl bg-emerald-100 text-emerald-600 flex items-center justify-center text-2xl">
              ⚕️
            </div>
            <div>
              <h2 className="text-lg font-semibold text-slate-800">Ask a preventive-health question</h2>
              <p className="text-sm text-slate-500 mt-1 max-w-md">
                Every answer is drawn only from referenced guidelines and cites its sources. If there's no source, it
                says so rather than guess.
              </p>
            </div>
          </div>
        ) : (
          <div className="flex-1 space-y-3 pb-24">
            {messages.map((m, i) => (
              <Message
                key={i}
                message={m}
                question={m.role === "assistant" ? messages[i - 1]?.content : undefined}
              />
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-white border border-slate-200 rounded-2xl px-4 py-3">
                  <Dots />
                </div>
              </div>
            )}
            <div ref={bottomRef} className="scroll-mb-24" />
          </div>
        )}

        {error && <p className="text-sm text-red-600 mt-3">{error}</p>}

        {/* Input area — suggested questions sit directly above the textbox and
            stay there (sticky), so they're always one tap away as you type. */}
        <div className="mt-4 sticky bottom-0 bg-slate-50 pt-2 pb-[max(0.75rem,env(safe-area-inset-bottom))]">
          <div className="mb-2 flex gap-2 overflow-x-auto pb-0.5 [scrollbar-width:none] [-ms-overflow-style:none] [&::-webkit-scrollbar]:hidden">
            {EXAMPLES.map((ex) => (
              <button
                key={ex}
                type="button"
                onClick={() => submit(ex)}
                disabled={loading}
                className="shrink-0 whitespace-nowrap text-sm border border-slate-200 bg-white rounded-full px-3.5 py-2 min-h-[40px] inline-flex items-center text-slate-600 hover:border-emerald-400 hover:text-emerald-700 disabled:opacity-40 transition-colors"
              >
                {ex}
              </button>
            ))}
          </div>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              submit(input);
            }}
            className="flex gap-2"
          >
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={loading}
              placeholder="Ask about vaccines, screenings, healthy habits…"
              className="flex-1 border border-slate-300 rounded-xl px-4 py-3 bg-white shadow-sm focus:outline-none focus:ring-2 focus:ring-emerald-400"
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="bg-emerald-600 text-white font-semibold rounded-xl px-5 hover:bg-emerald-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              Send
            </button>
          </form>
        </div>

        <p className="text-[11px] text-slate-400 text-center mt-3">
          Informational only, grounded in referenced guidelines — not a substitute for professional medical advice.
        </p>
      </main>
    </div>
  );
}
