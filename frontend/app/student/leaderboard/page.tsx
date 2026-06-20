"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { LeaderboardEntry } from "@/lib/types";

export default function LeaderboardPage() {
  const [entries, setEntries] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .getLeaderboard()
      .then((res) => setEntries(res.entries))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="min-h-screen bg-surface">
      <header className="border-b border-surface-border bg-surface-raised px-6 py-3">
        <div className="max-w-3xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link href="/student" className="text-xs text-slate-500 hover:text-slate-300">
              ← Innovation Hub
            </Link>
            <span className="text-surface-border">|</span>
            <span className="text-accent font-semibold text-sm tracking-wider">EXECUTION RANK</span>
          </div>
          <Link href="/enterprise/radar" className="text-xs text-slate-500 hover:text-accent">
            Enterprise radar →
          </Link>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-6 py-8 space-y-6">
        <div>
          <h1 className="text-xl font-semibold text-slate-100">Global Proof-of-Work Rank</h1>
          <p className="text-sm text-slate-500 mt-1">
            Platform-level Execution Points — earned on anonymous blind-audition challenges,
            decoupled from sponsor identity. Top performers surface to enterprise recruiters
            via reverse sourcing (demo).
          </p>
          <Link href="/student/trust" className="text-xs text-accent hover:underline mt-2 inline-block">
            How sponsor verification works →
          </Link>
        </div>

        {loading && <p className="text-slate-600 text-sm">Loading…</p>}

        <div className="space-y-2">
          {entries.map((e) => (
            <div
              key={e.rank}
              className="flex items-center gap-4 p-4 rounded-lg border border-surface-border bg-surface-raised"
            >
              <span className="text-2xl font-bold text-slate-600 w-8">#{e.rank}</span>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-slate-100">{e.display_name}</p>
                <p className="text-xs text-slate-500">{e.highlight}</p>
                <p className="text-[10px] text-slate-600 uppercase tracking-widest mt-1">
                  {e.track.replace("_", " ")}
                </p>
              </div>
              <div className="text-right">
                <p className="text-lg font-mono text-accent">{e.execution_points}</p>
                <p className="text-[10px] text-slate-600 uppercase">points</p>
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
