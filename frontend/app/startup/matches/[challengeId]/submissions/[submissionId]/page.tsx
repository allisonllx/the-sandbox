"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import type { SponsorSubmissionDetail } from "@/lib/types";
import { ScorecardView } from "@/components/ScorecardView";
import { SubmissionReviewPanel } from "@/components/SubmissionReviewPanel";

export default function SponsorSubmissionReviewPage() {
  const params = useParams();
  const challengeId = params.challengeId as string;
  const submissionId = params.submissionId as string;

  const [detail, setDetail] = useState<SponsorSubmissionDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .getSponsorSubmission(challengeId, submissionId)
      .then(setDetail)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load submission"))
      .finally(() => setLoading(false));
  }, [challengeId, submissionId]);

  const linkEntries = detail?.links ? Object.entries(detail.links).filter(([, v]) => v) : [];

  return (
    <div className="min-h-screen bg-surface">
      <header className="border-b border-surface-border bg-surface-raised px-6 py-3">
        <div className="max-w-5xl mx-auto flex items-center gap-3">
          <Link
            href={`/startup/matches/${challengeId}`}
            className="text-xs text-slate-500 hover:text-slate-300"
          >
            ← Match Radar
          </Link>
          <span className="text-surface-border">|</span>
          <span className="text-amber-500/90 font-semibold text-sm tracking-wider">
            SUBMISSION REVIEW
          </span>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-8 space-y-6">
        {loading && <p className="text-slate-600 text-sm">Loading…</p>}
        {error && (
          <p className="text-red-400 text-sm bg-red-500/10 border border-red-500/20 rounded px-3 py-2">
            {error}
          </p>
        )}

        {detail && (
          <>
            <div>
              <h1 className="text-xl font-semibold text-slate-100">{detail.candidate_id}</h1>
              <p className="text-sm text-slate-500 mt-1">
                Challenge <span className="text-slate-400">{detail.challenge_id}</span>
                {detail.submitted_at && (
                  <>
                    {" "}
                    · submitted{" "}
                    {new Date(detail.submitted_at).toLocaleString(undefined, {
                      dateStyle: "medium",
                      timeStyle: "short",
                    })}
                  </>
                )}
              </p>
              <p className="text-[10px] text-slate-600 uppercase tracking-widest mt-2">
                Read-only snapshot · blind-audition id
              </p>
            </div>

            {detail.scorecard && <ScorecardView scorecard={detail.scorecard} />}

            {linkEntries.length > 0 && (
              <div className="rounded-lg border border-surface-border bg-surface-raised/50 p-4 space-y-2">
                <p className="text-[11px] uppercase tracking-widest text-slate-500">External links</p>
                {linkEntries.map(([key, url]) => (
                  <a
                    key={key}
                    href={url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block text-xs text-accent hover:underline truncate"
                  >
                    {key}: {url}
                  </a>
                ))}
              </div>
            )}

            <SubmissionReviewPanel files={detail.files} />
          </>
        )}
      </main>
    </div>
  );
}
