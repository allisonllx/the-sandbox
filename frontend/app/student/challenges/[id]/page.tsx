"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import type { PublishedChallenge, SubmitResponse } from "@/lib/types";
import { MicroPRDView } from "@/components/MicroPRDView";
import { ChallengeWorkspace } from "@/components/ChallengeWorkspace";
import { ProductWorkspace } from "@/components/ProductWorkspace";
import { ScorecardView } from "@/components/ScorecardView";

export default function ChallengeWorkspacePage() {
  const params = useParams();
  const challengeId = params.id as string;

  const [challenge, setChallenge] = useState<PublishedChallenge | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [submitResult, setSubmitResult] = useState<SubmitResponse | null>(null);
  const [downloading, setDownloading] = useState(false);
  const [downloadingStarter, setDownloadingStarter] = useState(false);

  const isProduct = challenge?.track === "product_feature";

  useEffect(() => {
    api
      .getChallenge(challengeId)
      .then(setChallenge)
      .catch((e) => setError(e instanceof Error ? e.message : "Not found"))
      .finally(() => setLoading(false));
  }, [challengeId]);

  async function handleDownloadDataset() {
    setDownloading(true);
    try {
      const blob = await api.downloadDataset(challengeId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${challengeId}_sandbox.sqlite`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Download failed");
    } finally {
      setDownloading(false);
    }
  }

  async function handleDownloadStarter() {
    setDownloadingStarter(true);
    try {
      const blob = await api.downloadStarterZip(challengeId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${challengeId}_starter.zip`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Starter download failed");
    } finally {
      setDownloadingStarter(false);
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-surface flex items-center justify-center text-slate-600 text-sm">
        Loading challenge…
      </div>
    );
  }

  if (error && !challenge) {
    return (
      <div className="min-h-screen bg-surface flex flex-col items-center justify-center gap-4">
        <p className="text-red-400 text-sm">{error}</p>
        <Link href="/student" className="text-accent text-sm hover:underline">
          ← Back to challenges
        </Link>
      </div>
    );
  }

  if (!challenge) return null;

  return (
    <div className="h-screen bg-surface flex flex-col overflow-hidden">
      <header className="flex-shrink-0 border-b border-surface-border bg-surface-raised px-6 py-3">
        <div className="flex items-center justify-between max-w-[1600px] mx-auto gap-4">
          <div className="flex items-center gap-3 min-w-0">
            <Link href="/student" className="text-xs text-slate-500 hover:text-slate-300">
              ← Challenges
            </Link>
            <span className="text-surface-border">|</span>
            <span className="text-sm text-slate-200 font-medium truncate max-w-md">
              {challenge.title}
            </span>
            {challenge.brand_proxy && (
              <span className="text-[10px] text-slate-600 uppercase tracking-wider flex-shrink-0">
                {challenge.brand_proxy}
              </span>
            )}
          </div>
          <div className="flex gap-2 flex-shrink-0">
            <button
              type="button"
              onClick={() => void handleDownloadStarter()}
              disabled={downloadingStarter}
              className="text-xs px-3 py-1.5 rounded border border-surface-border text-slate-300
                hover:bg-surface-muted disabled:opacity-50"
            >
              {downloadingStarter ? "Downloading…" : "Starter ZIP"}
            </button>
            {!isProduct && (
              <button
                type="button"
                onClick={() => void handleDownloadDataset()}
                disabled={downloading || !challenge.dataset_ready}
                className="text-xs px-3 py-1.5 rounded border border-surface-border text-slate-300
                  hover:bg-surface-muted disabled:opacity-50"
              >
                {downloading ? "Downloading…" : "Dataset (.sqlite)"}
              </button>
            )}
          </div>
        </div>
      </header>

      <div className="flex flex-1 min-h-0 overflow-hidden max-w-[1600px] mx-auto w-full">
        <aside className="w-[380px] flex-shrink-0 border-r border-surface-border min-h-0 overflow-y-auto p-6">
          <MicroPRDView prd={challenge.microprd} />
          {!isProduct && challenge.dataset_anomalies.length > 0 && (
            <div className="mt-8 pt-6 border-t border-surface-border space-y-2">
              <h3 className="text-[11px] uppercase tracking-widest text-slate-500 font-semibold">
                Injected Anomalies
              </h3>
              <ul className="space-y-1">
                {challenge.dataset_anomalies.map((a, i) => (
                  <li key={i} className="text-xs text-amber-400/90 flex gap-2">
                    <span>⚠</span>
                    {a}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {isProduct && challenge.evaluation_focus && challenge.evaluation_focus.length > 0 && (
            <div className="mt-8 pt-6 border-t border-surface-border space-y-2">
              <h3 className="text-[11px] uppercase tracking-widest text-slate-500 font-semibold">
                Evaluation Focus
              </h3>
              <ul className="space-y-1">
                {challenge.evaluation_focus.map((focus) => (
                  <li key={focus} className="text-xs text-purple-400/90 flex gap-2">
                    <span>◎</span>
                    {focus}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </aside>

        <main className="flex-1 flex flex-col min-h-0 overflow-hidden p-6 gap-3">
          <div className="flex-1 min-h-0 overflow-hidden">
            {isProduct ? (
              <ProductWorkspace
                challengeId={challengeId}
                onSubmitResult={setSubmitResult}
                onError={setError}
              />
            ) : (
              <ChallengeWorkspace
                challengeId={challengeId}
                className="h-full"
                onSubmitResult={setSubmitResult}
                onError={setError}
              />
            )}
          </div>
          {error && (
            <p className="flex-shrink-0 text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded px-3 py-2">
              {error}
            </p>
          )}
          {submitResult && (
            <div className="flex-shrink-0 max-h-40 overflow-y-auto space-y-3">
              <div className="rounded-lg border border-green-500/30 bg-green-500/10 p-4 space-y-1">
                <p className="text-sm text-green-400 font-semibold">Submission received</p>
                <p className="text-xs text-slate-400">{submitResult.message}</p>
                <p className="text-[10px] text-slate-600 font-mono">
                  id: {submitResult.submission_id} · status: {submitResult.status}
                </p>
              </div>
              {submitResult.scorecard && <ScorecardView scorecard={submitResult.scorecard} />}
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
