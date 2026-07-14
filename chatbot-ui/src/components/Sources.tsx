import type { Source } from "../types";

export default function Sources({ sources }: { sources: Source[] }) {
  if (!sources.length) return null;
  return (
    <div className="mt-3 border-t border-slate-100 pt-2.5">
      <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400 mb-1.5">
        Sources ({sources.length})
      </p>
      <div className="space-y-1.5">
        {sources.map((s, i) => (
          <div key={i} className="flex items-start gap-2 text-xs">
            <span className="shrink-0 mt-0.5 rounded bg-emerald-100 text-emerald-700 font-mono px-1.5 py-0.5 text-[10px]">
              {s.id ?? "—"}
            </span>
            <div className="min-w-0">
              <span className="text-slate-700">{s.topic}</span>
              {s.source_url ? (
                <a
                  href={s.source_url}
                  target="_blank"
                  rel="noreferrer"
                  className="ml-1.5 text-emerald-600 hover:underline"
                >
                  {s.source_org}
                </a>
              ) : (
                <span className="ml-1.5 text-slate-400">{s.source_org}</span>
              )}
              {typeof s.score === "number" && (
                <span className="ml-1.5 text-slate-300">· {(s.score * 100).toFixed(0)}% match</span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
