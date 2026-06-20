"use client";

import Link from "next/link";
import type { PublishedChallenge } from "@/lib/types";

export function ChallengeCard({ challenge }: { challenge: PublishedChallenge }) {
  return (
    <Link
      href={`/student/challenges/${challenge.id}`}
      className="block p-5 rounded-lg border border-surface-border bg-surface-raised
        hover:border-accent/50 hover:bg-accent/5 transition-all"
    >
      <h3 className="text-sm font-semibold text-slate-100 mb-2">{challenge.title}</h3>
      <p className="text-xs text-slate-500 line-clamp-2 mb-3">{challenge.microprd.context}</p>
      <div className="flex items-center justify-between text-[10px] uppercase tracking-widest">
        <span className="text-green-400">● Live</span>
        <span className="text-slate-600">
          {challenge.dataset_anomalies.length} injected anomalies
        </span>
      </div>
    </Link>
  );
}
