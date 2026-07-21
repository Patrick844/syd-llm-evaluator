import { useEffect, useRef, useState } from "react";
import { ask, ApiError } from "./api";
import type { ChatMessage } from "./types";
import Message from "./components/Message";
import { track } from "./analytics";

const EXAMPLES = [
  "Do adults need a yearly flu vaccine?",
  "How much sleep do adults need?",
  "Who should get their blood pressure checked?",
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
    <div className="min-h-screen flex flex-col bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto max-w-3xl px-4 py-3 flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-emerald-600 text-white flex items-center justify-center text-lg">
            ⚕️
          </div>
          <div>
            <h1 className="font-semibold text-slate-900 leading-tight">Preventive Health Assistant</h1>
            <p className="text-xs text-slate-500">Answers grounded in referenced guidelines — with sources</p>
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
            <div className="flex flex-wrap justify-center gap-2 max-w-lg">
              {EXAMPLES.map((ex) => (
                <button
                  key={ex}
                  onClick={() => submit(ex)}
                  className="text-sm border border-slate-200 bg-white rounded-full px-4 py-2 text-slate-600 hover:border-emerald-400 hover:text-emerald-700 transition-colors"
                >
                  {ex}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="flex-1 space-y-3">
            {messages.map((m, i) => (
              <Message key={i} message={m} />
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-white border border-slate-200 rounded-2xl px-4 py-3">
                  <Dots />
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>
        )}

        {error && <p className="text-sm text-red-600 mt-3">{error}</p>}

        <form
          onSubmit={(e) => {
            e.preventDefault();
            submit(input);
          }}
          className="mt-4 flex gap-2 sticky bottom-4"
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

        <p className="text-[11px] text-slate-400 text-center mt-3">
          Informational only, grounded in referenced guidelines — not a substitute for professional medical advice.
        </p>
      </main>
    </div>
  );
}
