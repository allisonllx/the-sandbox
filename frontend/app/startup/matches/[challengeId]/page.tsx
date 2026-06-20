"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import type { SponsorMatchEntry } from "@/lib/types";

export default function StartupMatchesPage() {
  const params = useParams();
  const challengeId = params.challengeId as string;
  const [entries, setEntries] = useState<SponsorMatchEntry[]>([]);
  const [title, setTitle] = useState<string | null>(null);
  const [source, setSource] = useState<string>("demo");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .getSponsorMatches(challengeId)
      .then((res) => {
        setEntries(res.entries);
        setTitle(res.challenge_title ?? null);
        setSource(res.source);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load matches"))
      .finally(() => setLoading(false));
  }, [challengeId]);

  return (
    <div className="min-h-screen bg-surface">
      <header className="border-b border-surface-border bg-surface-raised px-6 py-3">
        <div className="max-w-3xl mx-auto flex items-center gap-3">
          <Link href="/startup" className="text-xs text-slate-500 hover:text-slate-300">
            ← CTO Dashboard
          </Link>
          <span className="text-surface-border">|</span>
          <span className="text-amber-500/90 font-semibold text-sm tracking-wider">
            SPONSOR MATCH RADAR
          </span>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-6 py-8 space-y-6">
        <div>
          <h1 className="text-xl font-semibold text-slate-100">Your Challenge Matches</h1>
          <p className="text-sm text-slate-500 mt-1">
            Candidates ranked by Execution Points on{" "}
            <span className="text-slate-400">{title ?? challengeId}</span> only. You do not see
            performers from other sponsors&apos; challenges.
          </p>
          <p className="text-[10px] text-slate-600 mt-2 uppercase tracking-widest">
            Source: {source} · Blind-audition IDs only
          </p>
        </div>

        {loading && <p className="text-slate-600 text-sm">Loading…</p>}
        {error && (
          <p className="text-red-400 text-sm bg-red-500/10 border border-red-500/20 rounded px-3 py-2">
            {error}
          </p>
        )}

        {!loading && !error && entries.length === 0 && (
          <p className="text-slate-500 text-sm border border-dashed border-surface-border rounded-lg p-6">
            No submissions yet. Students appear here after they submit solutions to your published
            challenge.
          </p>
        )}

        <div className="space-y-2">
          {entries.map((e) => (
            <div
              key={e.candidate_id}
              className="flex items-start gap-4 p-4 rounded-lg border border-amber-500/20 bg-amber-500/5"
            >
              <span className="text-xl font-bold text-slate-600 w-8">#{e.rank}</span>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-slate-100">{e.candidate_id}</p>
                <p className="text-xs text-slate-500 mt-1">{e.summary}</p>
                <p className="text-[10px] text-slate-600 uppercase tracking-widest mt-1">
                  {e.track.replace("_", " ")}
                </p>
              </div>
              <div className="text-right">
                <p className="text-lg font-mono text-amber-400">{e.execution_points}</p>
                <p className="text-[10px] text-slate-600 uppercase">pts</p>
              </div>
            </div>
          ))}
        </div>

        <p className="text-xs text-slate-600 border-t border-surface-border pt-4">
          Looking for platform-wide talent? That is the{" "}
          <Link href="/enterprise/radar" className="text-slate-500 hover:text-accent underline">
            Enterprise Radar
          </Link>{" "}
          subscription tier — not shown on the student leaderboard or sponsor view.
        </p>
      </main>
    </div>
  );
}
