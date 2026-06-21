"use client";

import { useState } from "react";
import type { BacklogItem, IntakeResponse } from "@/lib/types";
import { api } from "@/lib/api";

interface Props {
  onIntake: (item: BacklogItem) => void;
}

export function FounderIntakePanel({ onIntake }: Props) {
  const [open, setOpen] = useState(false);
  const [label, setLabel] = useState("Founder brief");
  const [statement, setStatement] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastResult, setLastResult] = useState<IntakeResponse | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!statement.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const result = await api.intake(statement.trim(), label.trim() || "Founder brief");
      setLastResult(result);
      const item = await api.getItem(result.item_id);
      onIntake(item);
      setStatement("");
      setOpen(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Intake failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mb-3 rounded-lg border border-surface-border bg-surface-raised overflow-hidden">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="w-full px-3 py-2.5 text-left text-[11px] uppercase tracking-widest text-slate-400 hover:text-slate-200 flex items-center justify-between"
      >
        <span>Describe a problem</span>
        <span className="text-slate-600">{open ? "−" : "+"}</span>
      </button>

      {open && (
        <form onSubmit={handleSubmit} className="px-3 pb-3 space-y-2 border-t border-surface-border pt-2">
          <p className="text-[10px] text-slate-500 leading-relaxed">
            Paste an internal problem brief. Sanitized locally before scoring — raw text never leaves this process.
          </p>
          <input
            type="text"
            value={label}
            onChange={(e) => setLabel(e.target.value)}
            placeholder="Source label"
            className="w-full text-xs px-2 py-1.5 rounded border border-surface-border bg-surface text-slate-300"
          />
          <textarea
            value={statement}
            onChange={(e) => setStatement(e.target.value)}
            placeholder="e.g. Our webhook retries duplicate charges when the gateway returns 502…"
            rows={4}
            className="w-full text-xs px-2 py-1.5 rounded border border-surface-border bg-surface text-slate-200 leading-relaxed resize-y min-h-[80px]"
          />
          {error && (
            <p className="text-[10px] text-red-400 bg-red-500/10 border border-red-500/20 rounded px-2 py-1">
              {error}
            </p>
          )}
          <button
            type="submit"
            disabled={loading || !statement.trim()}
            className="w-full text-xs py-2 rounded bg-accent/20 text-accent hover:bg-accent/30 disabled:opacity-40"
          >
            {loading ? "Sanitizing & scoring…" : "Add to backlog"}
          </button>
        </form>
      )}

      {lastResult && !open && (
        <p className="px-3 pb-2 text-[10px] text-slate-500">
          Last intake: {lastResult.tag} sensitivity · track {lastResult.suggested_track}
        </p>
      )}
    </div>
  );
}
