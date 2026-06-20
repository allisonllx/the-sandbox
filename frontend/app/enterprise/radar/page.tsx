"use client";

import Link from "next/link";

const MOCK_CANDIDATES = [
  {
    id: "A7F2",
    rank: "Top 1%",
    track: "Technical",
    points: 118,
    signal: "Challenge #demo-003 · Async event processor diagnosis",
  },
  {
    id: "B3K9",
    rank: "Top 2%",
    track: "Product Feature",
    points: 104,
    signal: "Challenge #demo-005 · Anonymous Series A · Equipment discovery IA",
  },
  {
    id: "C1M4",
    rank: "Top 3%",
    track: "Technical",
    points: 96,
    signal: "Challenge #demo-006 · Platform traffic spike replay",
  },
];

export default function EnterpriseRadarPage() {
  return (
    <div className="min-h-screen bg-surface">
      <header className="border-b border-surface-border bg-surface-raised px-6 py-3">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-accent font-semibold text-sm tracking-wider">ENTERPRISE RADAR</span>
            <span className="text-surface-border">|</span>
            <span className="text-slate-400 text-xs uppercase tracking-widest">Demo — reverse sourcing</span>
          </div>
          <Link href="/student/leaderboard" className="text-xs text-slate-500 hover:text-accent">
            ← Public rank
          </Link>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-8 space-y-6">
        <div>
          <h1 className="text-xl font-semibold text-slate-100">Verified Talent Radar</h1>
          <p className="text-sm text-slate-500 mt-1">
            Large companies don&apos;t post challenges — they buy access to platform-verified
            Execution Points. A student solves an anonymous startup bounty; a tier-1 recruiter
            sees the signal tomorrow. No sponsor identity is exposed (demo stub).
          </p>
        </div>

        <div className="grid gap-3">
          {MOCK_CANDIDATES.map((c) => (
            <div
              key={c.id}
              className="p-5 rounded-lg border border-surface-border bg-surface-raised flex flex-wrap items-center justify-between gap-4"
            >
              <div>
                <p className="text-sm font-semibold text-slate-100">Candidate {c.id}</p>
                <p className="text-xs text-purple-400 mt-0.5">{c.rank} · {c.track}</p>
                <p className="text-xs text-slate-500 mt-2">{c.signal}</p>
              </div>
              <div className="text-right">
                <p className="text-xl font-mono text-accent">{c.points}</p>
                <p className="text-[10px] text-slate-600 uppercase">execution pts</p>
              </div>
            </div>
          ))}
        </div>

        <p className="text-xs text-slate-600 border-t border-surface-border pt-4">
          Deferrals: no auth, no FAANG API, no hiring contracts — hackathon narrative only.
        </p>
      </main>
    </div>
  );
}
