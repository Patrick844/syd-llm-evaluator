import type { ReactNode } from "react";
import type { Source } from "../types";

// Trivial words we don't want to highlight — they'd match almost every snippet.
const STOPWORDS = new Set([
  "the", "a", "an", "is", "are", "was", "were", "be", "been", "do", "does",
  "did", "i", "you", "we", "they", "he", "she", "it", "me", "my", "your",
  "need", "should", "how", "much", "many", "who", "when", "what", "why",
  "where", "which", "can", "could", "will", "would", "of", "to", "for",
  "and", "or", "in", "on", "at", "with", "about", "get", "getting", "have",
  "has", "am", "any", "some", "that", "this", "there", "from", "by",
]);

/** Lowercase word set of the user's question, minus stopwords/short tokens. */
function queryTerms(question?: string): Set<string> {
  const terms = new Set<string>();
  if (!question) return terms;
  for (const raw of question.toLowerCase().split(/[^a-z0-9]+/)) {
    if (raw.length > 2 && !STOPWORDS.has(raw)) terms.add(raw);
  }
  return terms;
}

/** Render a snippet, emphasising words that overlap the user's question. */
function highlight(text: string, terms: Set<string>): ReactNode[] {
  if (!terms.size) return [text];
  // Split on word boundaries but keep the separators (spaces/punctuation).
  const tokens = text.split(/(\b)/);
  return tokens.map((tok, i) => {
    const norm = tok.toLowerCase().replace(/[^a-z0-9]/g, "");
    if (norm.length > 2 && terms.has(norm)) {
      return (
        <mark
          key={i}
          className="bg-emerald-100 text-emerald-800 font-medium rounded px-0.5"
        >
          {tok}
        </mark>
      );
    }
    return tok;
  });
}

// A retrieved chunk must clear this cosine score to count as a real citation.
// (The backend retrieves above a looser 0.2 floor; anything between the two is
// "found but not relevant enough" — shown dimmed, not as a confident source.)
const RELEVANCE_THRESHOLD = 0.4;

function SourceRow({ s, terms, dim }: { s: Source; terms: Set<string>; dim?: boolean }) {
  return (
    <div className={`flex items-start gap-2 text-xs ${dim ? "opacity-50" : ""}`}>
      <span className="shrink-0 mt-0.5 rounded bg-emerald-100 text-emerald-700 font-mono px-1.5 py-0.5 text-[10px]">
        {s.id ?? "—"}
      </span>
      <div className="min-w-0">
        <span className="text-slate-700">{s.topic}</span>
        {s.source_url ? (
          <a href={s.source_url} target="_blank" rel="noreferrer" className="ml-1.5 text-emerald-600 hover:underline break-words">
            {s.source_org}
          </a>
        ) : (
          <span className="ml-1.5 text-slate-400">{s.source_org}</span>
        )}
        {typeof s.score === "number" && (
          <span className="ml-1.5 text-slate-300">· {(s.score * 100).toFixed(0)}% match</span>
        )}
        {s.guideline && (
          <p className="mt-0.5 text-slate-500 leading-snug break-words">{highlight(s.guideline, terms)}</p>
        )}
      </div>
    </div>
  );
}

export default function Sources({
  sources,
  question,
}: {
  sources: Source[];
  question?: string;
}) {
  if (!sources.length) return null;
  const terms = queryTerms(question);
  const scored = sources.map((s) => (typeof s.score === "number" ? s.score : 0));
  const best = Math.max(...scored);
  const relevant = sources.filter((s) => (s.score ?? 0) >= RELEVANCE_THRESHOLD);
  const below = sources.filter((s) => (s.score ?? 0) < RELEVANCE_THRESHOLD);

  // Nothing cleared the bar → this was a refusal/uncertain answer. Show the
  // thresholding decision itself instead of a list of weak, misleading matches.
  if (!relevant.length) {
    return (
      <div className="mt-3 border-t border-slate-100 pt-2.5">
        <p className="text-xs text-slate-500">
          🔒 No sufficiently relevant source found (best match:{" "}
          <span className="font-medium text-slate-600">{(best * 100).toFixed(0)}%</span>,
          below the {RELEVANCE_THRESHOLD * 100}% relevance threshold).
        </p>
      </div>
    );
  }

  return (
    <div className="mt-3 border-t border-slate-100 pt-2.5">
      <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400 mb-1.5">
        Sources ({relevant.length})
      </p>
      <div className="space-y-2">
        {relevant.map((s, i) => (
          <SourceRow key={i} s={s} terms={terms} />
        ))}
      </div>
      {below.length > 0 && (
        <details className="mt-2">
          <summary className="cursor-pointer text-[11px] text-slate-400 hover:text-slate-500">
            {below.length} more below the relevance cutoff
          </summary>
          <div className="mt-2 space-y-2">
            {below.map((s, i) => (
              <SourceRow key={i} s={s} terms={terms} dim />
            ))}
          </div>
        </details>
      )}
    </div>
  );
}
