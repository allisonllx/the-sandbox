"use client";

import Link from "next/link";
import type { ChallengeTrack, PublishedChallenge } from "@/lib/types";

const TRACK_LABELS: Record<ChallengeTrack, string> = {
  technical: "Technical",
  product_feature: "Product Feature",
  automation: "Automation",
  ai_governance: "AI Governance",
  strategy: "Strategy",
};

const TRACK_COLORS: Record<ChallengeTrack, string> = {
  technical: "text-blue-400 bg-blue-500/10 border-blue-500/30",
  product_feature: "text-purple-400 bg-purple-500/10 border-purple-500/30",
  automation: "text-slate-500 bg-slate-500/10 border-slate-500/30",
  ai_governance: "text-slate-500 bg-slate-500/10 border-slate-500/30",
  strategy: "text-slate-500 bg-slate-500/10 border-slate-500/30",
};

export function ChallengeCard({ challenge }: { challenge: PublishedChallenge }) {
  const track = challenge.track ?? "technical";
  const trackLabel = TRACK_LABELS[track] ?? "Technical";
  const trackColor = TRACK_COLORS[track] ?? TRACK_COLORS.technical;

  return (
    <Link
      href={`/student/challenges/${challenge.id}`}
      className="block p-5 rounded-lg border border-surface-border bg-surface-raised
        hover:border-accent/50 hover:bg-accent/5 transition-all"
    >
      <div className="flex items-start justify-between gap-3 mb-2">
        <h3 className="text-sm font-semibold text-slate-100">{challenge.title}</h3>
        <span
          className={`flex-shrink-0 text-[10px] uppercase tracking-widest px-2 py-0.5 rounded border ${trackColor}`}
        >
          {trackLabel}
        </span>
      </div>
      {challenge.brand_proxy && (
        <p className="text-[10px] text-slate-600 mb-2 uppercase tracking-wider">
          {challenge.brand_proxy}
        </p>
      )}
      <p className="text-xs text-slate-500 line-clamp-2 mb-3">{challenge.microprd.context}</p>
      {challenge.evaluation_focus && challenge.evaluation_focus.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-3">
          {challenge.evaluation_focus.slice(0, 3).map((focus) => (
            <span
              key={focus}
              className="text-[10px] px-1.5 py-0.5 rounded bg-surface-muted text-slate-500"
            >
              {focus}
            </span>
          ))}
        </div>
      )}
      <div className="flex items-center justify-between text-[10px] uppercase tracking-widest">
        <span className="text-green-400">● Live</span>
        <span className="text-slate-600">
          {track === "product_feature"
            ? "Prototype + DESIGN.md"
            : `${challenge.dataset_anomalies.length} injected anomalies`}
        </span>
      </div>
    </Link>
  );
}
