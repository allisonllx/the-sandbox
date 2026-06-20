"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { PublishedChallenge } from "@/lib/types";
import { ChallengeCard } from "@/components/ChallengeCard";

export default function StudentBrowsePage() {
  const [challenges, setChallenges] = useState<PublishedChallenge[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .listChallenges()
      .then(setChallenges)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="min-h-screen bg-surface">
      <header className="border-b border-surface-border bg-surface-raised px-6 py-3">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-accent font-semibold text-sm tracking-wider">SANDBOX</span>
            <span className="text-surface-border">|</span>
            <span className="text-slate-400 text-xs uppercase tracking-widest">Challenges</span>
          </div>
          <Link href="/startup" className="text-xs text-slate-500 hover:text-slate-300">
            CTO Dashboard →
          </Link>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-8 space-y-6">
        <div>
          <h1 className="text-xl font-semibold text-slate-100">Public Challenges</h1>
          <p className="text-sm text-slate-500 mt-1">
            Real engineering problems from growth-stage startups — sanitized and de-risked.
          </p>
        </div>

        {loading && <p className="text-slate-600 text-sm">Loading challenges…</p>}
        {error && (
          <p className="text-red-400 text-sm bg-red-500/10 border border-red-500/20 rounded-lg p-4">
            {error}
            <span className="block text-slate-500 mt-1 text-xs">
              Is the backend running? Publish a challenge from /startup first.
            </span>
          </p>
        )}
        {!loading && !error && challenges.length === 0 && (
          <p className="text-slate-500 text-sm">
            No published challenges yet. A founder must approve one from the{" "}
            <Link href="/startup" className="text-accent hover:underline">
              CTO dashboard
            </Link>
            .
          </p>
        )}
        <div className="grid gap-3">
          {challenges.map((c) => (
            <ChallengeCard key={c.id} challenge={c} />
          ))}
        </div>
      </main>
    </div>
  );
}
