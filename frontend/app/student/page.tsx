"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { ChallengeTrack, PublishedChallenge } from "@/lib/types";
import { ChallengeCard } from "@/components/ChallengeCard";

type TrackFilter = "all" | ChallengeTrack | "coming_soon";

const TABS: { id: TrackFilter; label: string }[] = [
  { id: "all", label: "All" },
  { id: "technical", label: "Technical" },
  { id: "product_feature", label: "Product Feature" },
  { id: "coming_soon", label: "Coming Soon" },
];

export default function StudentBrowsePage() {
  const [challenges, setChallenges] = useState<PublishedChallenge[]>([]);
  const [activeTab, setActiveTab] = useState<TrackFilter>("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    const trackParam =
      activeTab === "all" || activeTab === "coming_soon"
        ? undefined
        : (activeTab as ChallengeTrack);

    api
      .listChallenges(trackParam)
      .then(setChallenges)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load"))
      .finally(() => setLoading(false));
  }, [activeTab]);

  const visible =
    activeTab === "coming_soon"
      ? []
      : activeTab === "all"
        ? challenges
        : challenges.filter((c) => (c.track ?? "technical") === activeTab);

  return (
    <div className="min-h-screen bg-surface">
      <header className="border-b border-surface-border bg-surface-raised px-6 py-3">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-accent font-semibold text-sm tracking-wider">INNOVATION HUB</span>
            <span className="text-surface-border">|</span>
            <span className="text-slate-400 text-xs uppercase tracking-widest">Challenges</span>
          </div>
          <Link href="/startup" className="text-xs text-slate-500 hover:text-slate-300">
            CTO Dashboard →
          </Link>
          <Link href="/student/leaderboard" className="text-xs text-slate-500 hover:text-accent">
            Execution Rank
          </Link>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-8 space-y-6">
        <div>
          <h1 className="text-xl font-semibold text-slate-100">Innovation Hub</h1>
          <p className="text-sm text-slate-500 mt-1">
            Technical debugging sprints and product feature challenges from growth-stage startups —
            sanitized and de-risked.
          </p>
        </div>

        <div className="flex flex-wrap gap-2 border-b border-surface-border pb-4">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id)}
              className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
                activeTab === tab.id
                  ? "border-accent bg-accent/10 text-accent"
                  : "border-surface-border text-slate-500 hover:text-slate-300"
              }`}
            >
              {tab.label}
            </button>
          ))}
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

        {activeTab === "coming_soon" && !loading && (
          <div className="rounded-lg border border-surface-border bg-surface-raised p-6 space-y-3">
            <p className="text-sm text-slate-400">More innovation tracks are on the roadmap:</p>
            <ul className="text-xs text-slate-500 space-y-1">
              <li>Automation — workflow and tooling challenges</li>
              <li>AI Governance — policy and guardrail design</li>
              <li>Strategy — market and portfolio reasoning</li>
            </ul>
          </div>
        )}

        {!loading && !error && activeTab !== "coming_soon" && visible.length === 0 && (
          <p className="text-slate-500 text-sm">
            No published challenges in this track yet. A founder must approve one from the{" "}
            <Link href="/startup" className="text-accent hover:underline">
              CTO dashboard
            </Link>
            .
          </p>
        )}

        <div className="grid gap-3">
          {visible.map((c) => (
            <ChallengeCard key={c.id} challenge={c} />
          ))}
        </div>
      </main>
    </div>
  );
}
