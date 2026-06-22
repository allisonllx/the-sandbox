"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { SanitizedMetadata, TechScores } from "@/lib/types";
import {
  clearPendingUpload,
  loadPendingUpload,
  type PendingUpload,
} from "@/lib/uploadSession";

type StepId = "sanitize" | "score" | "done";
type StepStatus = "pending" | "active" | "done" | "error";

interface StepState {
  id: StepId;
  label: string;
  detail: string;
  status: StepStatus;
}

function tagColor(tag: string) {
  if (tag === "red") return "text-red-400";
  if (tag === "yellow") return "text-amber-400";
  return "text-green-400";
}

export default function StartupUploadLoadingPage() {
  const router = useRouter();
  const [payload, setPayload] = useState<PendingUpload | null>(null);
  const [steps, setSteps] = useState<StepState[]>([
    {
      id: "sanitize",
      label: "Privacy sanitize",
      detail: "POST /api/v1/proxy/sanitize — strip PII, extract metadata",
      status: "pending",
    },
    {
      id: "score",
      label: "Sensitivity pass",
      detail: "POST /api/v1/triage/score — severity, friction, sensitivity",
      status: "pending",
    },
    {
      id: "done",
      label: "Backlog",
      detail: "Item ready for preview & publish",
      status: "pending",
    },
  ]);
  const [metadata, setMetadata] = useState<SanitizedMetadata | null>(null);
  const [scores, setScores] = useState<TechScores | null>(null);
  const [tag, setTag] = useState<string | null>(null);
  const [itemId, setItemId] = useState<string | null>(null);
  const [fatalError, setFatalError] = useState<string | null>(null);

  function setStepStatus(id: StepId, status: StepStatus) {
    setSteps((prev) => prev.map((s) => (s.id === id ? { ...s, status } : s)));
  }

  useEffect(() => {
    const pending = loadPendingUpload();
    if (!pending) {
      setFatalError("No upload in progress. Start from the upload page.");
      return;
    }
    setPayload(pending);

    let cancelled = false;

    async function run() {
      try {
        setStepStatus("sanitize", "active");
        const sanitized = await api.sanitize(pending!.content, pending!.format);
        if (cancelled) return;
        setMetadata(sanitized.metadata);
        setStepStatus("sanitize", "done");

        setStepStatus("score", "active");
        const scored = await api.scoreMetadata(sanitized.metadata, pending!.sourceLabel);
        if (cancelled) return;
        setScores(scored.scores);
        setTag(scored.tag);
        setItemId(scored.item_id);
        setStepStatus("score", "done");
        setStepStatus("done", "done");

        clearPendingUpload();

        window.setTimeout(() => {
          if (!cancelled) {
            router.replace(`/startup?select=${scored.item_id}`);
          }
        }, 1800);
      } catch (err) {
        if (cancelled) return;
        const msg = err instanceof Error ? err.message : "Processing failed";
        setFatalError(msg);
        setSteps((prev) =>
          prev.map((s) =>
            s.status === "active" || s.status === "pending" ? { ...s, status: "error" } : s
          )
        );
      }
    }

    void run();
    return () => {
      cancelled = true;
    };
  }, [router]);

  return (
    <div className="min-h-screen bg-surface flex flex-col">
      <header className="border-b border-surface-border bg-surface-raised px-6 py-3">
        <div className="max-w-lg mx-auto">
          <span className="text-slate-400 text-xs uppercase tracking-widest">Processing upload</span>
        </div>
      </header>

      <main className="flex-1 flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-lg space-y-6">
          {payload && (
            <div className="text-center">
              <p className="text-sm text-slate-300">{payload.sourceLabel}</p>
              <p className="text-[11px] text-slate-500 mt-1">
                {payload.kind === "logs" ? "Log ingest" : "Task description"}
                {payload.fileName ? ` · ${payload.fileName}` : ""}
              </p>
            </div>
          )}

          <ul className="space-y-3">
            {steps.map((step) => (
              <li
                key={step.id}
                className={`flex gap-3 items-start rounded-lg border px-4 py-3 ${
                  step.status === "active"
                    ? "border-accent/40 bg-accent/5"
                    : step.status === "done"
                      ? "border-green-500/30 bg-green-500/5"
                      : step.status === "error"
                        ? "border-red-500/30 bg-red-500/5"
                        : "border-surface-border bg-surface-raised/30"
                }`}
              >
                <StepIcon status={step.status} />
                <div className="min-w-0 flex-1">
                  <p className="text-sm text-slate-200">{step.label}</p>
                  <p className="text-[10px] text-slate-500 mt-0.5 font-mono">{step.detail}</p>
                </div>
              </li>
            ))}
          </ul>

          {metadata && (
            <div className="rounded-lg border border-surface-border bg-surface-raised/50 px-4 py-3 text-[11px] text-slate-400 space-y-1">
              <p>
                Fields detected:{" "}
                <span className="text-slate-300">{metadata.fields.length}</span>
                {metadata.approximate_row_scale != null && (
                  <>
                    {" "}
                    · row scale ~{" "}
                    <span className="text-slate-300">{metadata.approximate_row_scale}</span>
                  </>
                )}
              </p>
              {metadata.pii_detections.length > 0 && (
                <p>
                  PII stripped:{" "}
                  {metadata.pii_detections.map((p) => p.pii_type).join(", ")}
                </p>
              )}
            </div>
          )}

          {scores && tag && (
            <div className="rounded-lg border border-surface-border bg-surface-raised/50 px-4 py-3 text-center">
              <p className={`text-sm font-medium uppercase tracking-wider ${tagColor(tag)}`}>
                {tag} sensitivity
              </p>
              <p className="text-[11px] text-slate-500 mt-2 font-mono">
                S{scores.severity} · F{scores.friction} · Sen{scores.sensitivity}
              </p>
              <p className="text-xs text-slate-400 mt-2">{scores.suggested_title}</p>
            </div>
          )}

          {itemId && !fatalError && (
            <p className="text-center text-xs text-slate-500">Opening backlog…</p>
          )}

          {fatalError && (
            <div className="text-center space-y-3">
              <p className="text-sm text-red-400">{fatalError}</p>
              <Link
                href="/startup/upload"
                className="inline-block text-xs text-accent hover:underline"
              >
                ← Try again
              </Link>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

function StepIcon({ status }: { status: StepStatus }) {
  if (status === "active") {
    return (
      <span className="mt-0.5 w-4 h-4 rounded-full border-2 border-accent border-t-transparent animate-spin flex-shrink-0" />
    );
  }
  if (status === "done") {
    return <span className="mt-0.5 text-green-400 flex-shrink-0">✓</span>;
  }
  if (status === "error") {
    return <span className="mt-0.5 text-red-400 flex-shrink-0">✕</span>;
  }
  return <span className="mt-0.5 w-4 h-4 rounded-full border border-surface-border flex-shrink-0" />;
}
