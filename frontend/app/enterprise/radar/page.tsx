"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { EnterpriseRadarEntry } from "@/lib/types";

export default function EnterpriseRadarPage() {
  const [entries, setEntries] = useState<EnterpriseRadarEntry[]>([]);
  const [tier, setTier] = useState("Top 1% platform-wide");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .getEnterpriseRadar()
      .then((res) => {
        setEntries(res.entries);
        setTier(res.tier);
      })
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="min-h-screen bg-surface">
      <header className="border-b border-surface-border bg-surface-raised px-6 py-3">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-accent font-semibold text-sm tracking-wider">ENTERPRISE RADAR</span>
            <span className="text-surface-border">|</span>
            <span className="text-slate-400 text-xs uppercase tracking-widest">
              Subscription — platform-wide
            </span>
          </div>
          <Link href="/student" className="text-xs text-slate-500 hover:text-accent">
            Student hub →
          </Link>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-8 space-y-6">
        <div>
          <h1 className="text-xl font-semibold text-slate-100">Verified Talent Radar</h1>
          <p className="text-sm text-slate-500 mt-1">
            {tier} performers aggregated across <strong>all</strong> blind-audition challenges on
            the platform. Large enterprises subscribe to this view; startup sponsors use{" "}
            <Link href="/startup" className="text-accent hover:underline">
              Match Radar
            </Link>{" "}
            for their own challenge only.
          </p>
        </div>

        {loading && <p className="text-slate-600 text-sm">Loading…</p>}

        <div className="grid gap-3">
          {entries.map((c) => (
            <div
              key={c.candidate_id}
              className="p-5 rounded-lg border border-surface-border bg-surface-raised flex flex-wrap items-center justify-between gap-4"
            >
              <div>
                <p className="text-sm font-semibold text-slate-100">Candidate {c.candidate_id}</p>
                <p className="text-xs text-purple-400 mt-0.5">
                  {c.rank_label} · {c.track.replace("_", " ")}
                </p>
                <p className="text-xs text-slate-500 mt-2">{c.platform_signal}</p>
              </div>
              <div className="text-right">
                <p className="text-xl font-mono text-accent">{c.execution_points}</p>
                <p className="text-[10px] text-slate-600 uppercase">execution pts</p>
              </div>
            </div>
          ))}
        </div>

        <p className="text-xs text-slate-600 border-t border-surface-border pt-4">
          Demo stub — no auth, no ATS integration. Sponsor identity is never exposed.
        </p>
      </main>
    </div>
  );
}
