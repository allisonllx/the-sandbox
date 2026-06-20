"use client";

import type { BacklogItem } from "@/lib/types";
import { SensitivityBadge } from "./SensitivityBadge";
import { ScoreBar } from "./ScoreBar";

interface BacklogCardProps {
  item: BacklogItem;
  selected: boolean;
  onClick: () => void;
}

const STATUS_LABEL: Record<string, string> = {
  pending: "Pending Review",
  reviewing: "Under Review",
  approved: "Approved",
  published: "Published",
};

export function BacklogCard({ item, selected, onClick }: BacklogCardProps) {
  const scores = item.scores;
  const tag = item.tag ?? "green";

  return (
    <button
      onClick={onClick}
      className={`w-full text-left p-4 rounded-lg border transition-all duration-150 space-y-3
        ${selected
          ? "border-accent bg-accent/10"
          : "border-surface-border bg-surface-raised hover:border-surface-muted hover:bg-surface-muted/30"
        }`}
    >
      {/* Header row */}
      <div className="flex items-start justify-between gap-2">
        <p className="text-sm font-semibold text-slate-100 leading-snug flex-1">
          {scores?.suggested_title ?? "Untitled Challenge"}
        </p>
        {item.tag && <SensitivityBadge tag={tag} />}
      </div>

      {/* Source label */}
      <p className="text-[11px] text-slate-500 truncate">{item.source_label}</p>

      {/* Score bars */}
      {scores && (
        <div className="space-y-2">
          <ScoreBar label="Severity" value={scores.severity} color="bg-rose-500" />
          <ScoreBar label="Friction" value={scores.friction} color="bg-amber-500" />
          <ScoreBar label="Sensitivity" value={scores.sensitivity} color="bg-violet-500" />
        </div>
      )}

      {/* Status chip */}
      <div className="flex items-center justify-between">
        <span className="text-[10px] text-slate-500 uppercase tracking-widest">
          {STATUS_LABEL[item.status] ?? item.status}
        </span>
        <span className="text-[10px] text-slate-600">
          {item.metadata.fields.length} fields · {item.metadata.approximate_row_scale?.toLocaleString() ?? "?"} rows
        </span>
      </div>
    </button>
  );
}
