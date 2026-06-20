import type { Scorecard } from "@/lib/types";

function DimensionBars({ dimensions }: { dimensions: Record<string, number> }) {
  const entries = Object.entries(dimensions ?? {});
  if (entries.length === 0) return null;

  return (
    <div className="space-y-3">
      {entries.map(([label, score]) => (
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
  );
}

export function ScorecardView({ scorecard }: { scorecard: Scorecard }) {
  const platformDims = scorecard.platform?.dimensions ?? scorecard.dimensions ?? {};
  const sponsorDims = scorecard.sponsor?.dimensions ?? {};

  return (
    <div className="rounded-lg border border-accent/30 bg-accent/5 p-4 space-y-4">
      <div>
        <p className="text-sm font-semibold text-accent">Assessor Scorecard</p>
        <p className="text-xs text-slate-400 mt-1">{scorecard.summary}</p>
        {scorecard.execution_points != null && (
          <p className="text-xs text-amber-400/90 mt-2 font-mono">
            +{scorecard.execution_points} Execution Points — platform signal only (global rank)
          </p>
        )}
        {scorecard.sponsor_fit_score != null && (
          <p className="text-xs text-slate-500 mt-1 font-mono">
            Sponsor fit {scorecard.sponsor_fit_score}/100 — used for Match Radar on this challenge
          </p>
        )}
      </div>

      {scorecard.interview_pass_earned && (
        <div className="rounded border border-green-500/40 bg-green-500/10 px-3 py-2 text-xs text-green-400 font-semibold">
          Interview Pass earned (demo) — platform + sponsor fit ≥ benchmark{" "}
          {scorecard.interview_benchmark ?? 75}
        </div>
      )}

      {Object.keys(platformDims).length > 0 && (
        <div className="space-y-2">
          <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
            Platform Signal
          </p>
          <DimensionBars dimensions={platformDims} />
        </div>
      )}

      {Object.keys(sponsorDims).length > 0 && (
        <div className="space-y-2 pt-2 border-t border-surface-border">
          <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
            Sponsor Fit
          </p>
          {scorecard.sponsor?.summary && (
            <p className="text-xs text-slate-400">{scorecard.sponsor.summary}</p>
          )}
          <DimensionBars dimensions={sponsorDims} />
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
