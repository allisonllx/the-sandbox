import type { Scorecard } from "@/lib/types";

export function ScorecardView({ scorecard }: { scorecard: Scorecard }) {
  const dimensions = Object.entries(scorecard.dimensions ?? {});

  return (
    <div className="rounded-lg border border-accent/30 bg-accent/5 p-4 space-y-4">
      <div>
        <p className="text-sm font-semibold text-accent">Assessor Scorecard</p>
        <p className="text-xs text-slate-400 mt-1">{scorecard.summary}</p>
      </div>

      {dimensions.length > 0 && (
        <div className="space-y-3">
          {dimensions.map(([label, score]) => (
            <div key={label} className="space-y-1">
              <div className="flex justify-between text-xs">
                <span className="text-slate-300">{label}</span>
                <span className="text-slate-500 font-mono">{score}/100</span>
              </div>
              <div className="h-1.5 rounded-full bg-surface-border overflow-hidden">
                <div
                  className="h-full rounded-full bg-accent transition-all"
                  style={{ width: `${Math.min(100, Math.max(0, score))}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      )}

      {scorecard.notes && scorecard.notes.length > 0 && (
        <ul className="space-y-1 pt-2 border-t border-surface-border">
          {scorecard.notes.map((note, i) => (
            <li key={i} className="text-[11px] text-slate-500 flex gap-2">
              <span className="text-slate-600">·</span>
              {note}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
