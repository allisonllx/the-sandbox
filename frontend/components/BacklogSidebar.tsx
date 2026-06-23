"use client";

import { useEffect, useRef, useState } from "react";
import type { BacklogItem } from "@/lib/types";
import { BacklogCard } from "./BacklogCard";
import { FounderIntakePanel } from "./FounderIntakePanel";

const TRIAGE_STATUSES = new Set(["pending", "reviewing", "approved"]);

function partitionBacklog(items: BacklogItem[]) {
  const triage: BacklogItem[] = [];
  const live: BacklogItem[] = [];
  const closed: BacklogItem[] = [];
  for (const item of items) {
    if (TRIAGE_STATUSES.has(item.status)) {
      triage.push(item);
    } else if (item.status === "published") {
      live.push(item);
    } else if (item.status === "closed") {
      closed.push(item);
    }
  }
  return { triage, live, closed };
}

function CollapsibleSection({
  title,
  count,
  open,
  onToggle,
  emptyMessage,
  children,
}: {
  title: string;
  count: number;
  open: boolean;
  onToggle: () => void;
  emptyMessage?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="border-b border-surface-border/80 last:border-b-0">
      <button
        type="button"
        onClick={onToggle}
        className="w-full flex items-center justify-between px-4 py-2.5 text-left
          hover:bg-surface-muted/30 transition-colors"
      >
        <span className="text-[10px] uppercase tracking-widest text-slate-500 font-semibold">
          {title}
        </span>
        <span className="flex items-center gap-2 text-[10px] text-slate-600">
          <span>{count}</span>
          <span className="text-slate-500">{open ? "▾" : "▸"}</span>
        </span>
      </button>
      {open && (
        <div className="px-3 pb-3 space-y-2">
          {count === 0 && emptyMessage ? (
            <p className="text-[11px] text-slate-600 px-1 py-2">{emptyMessage}</p>
          ) : (
            children
          )}
        </div>
      )}
    </div>
  );
}

export function BacklogSidebar({
  items,
  selectedId,
  loading,
  error,
  onSelect,
  onIntake,
}: {
  items: BacklogItem[];
  selectedId: string | null;
  loading: boolean;
  error: string | null;
  onSelect: (id: string) => void;
  onIntake: (item: BacklogItem) => void;
}) {
  const { triage, live, closed } = partitionBacklog(items);
  const [triageOpen, setTriageOpen] = useState(true);
  const [liveOpen, setLiveOpen] = useState(live.length > 0);
  const [closedOpen, setClosedOpen] = useState(false);
  const prevLiveCount = useRef(live.length);
  const prevClosedCount = useRef(closed.length);

  useEffect(() => {
    if (live.length > prevLiveCount.current) {
      setLiveOpen(true);
    }
    prevLiveCount.current = live.length;
  }, [live.length]);

  useEffect(() => {
    if (closed.length > prevClosedCount.current) {
      setClosedOpen(true);
    }
    prevClosedCount.current = closed.length;
  }, [closed.length]);

  return (
    <aside className="w-80 flex-shrink-0 border-r border-surface-border bg-surface flex flex-col min-h-0">
      <div className="flex-shrink-0 px-4 py-3 border-b border-surface-border">
        <p className="text-[11px] text-slate-500 uppercase tracking-widest">CTO Backlog</p>
      </div>

      <div className="flex-shrink-0 p-3 border-b border-surface-border">
        <FounderIntakePanel onIntake={onIntake} />
      </div>

      {loading && (
        <div className="text-center py-12 text-slate-600 text-sm">Loading…</div>
      )}

      {error && (
        <div className="m-3 text-center text-red-400 text-xs bg-red-500/10 border border-red-500/20 rounded-lg p-4">
          {error}
          <br />
          <span className="text-slate-500 mt-1 block">Is the backend running on :8000?</span>
        </div>
      )}

      {!loading && !error && (
        <div className="flex-1 min-h-0 overflow-y-auto">
          <CollapsibleSection
            title="In triage"
            count={triage.length}
            open={triageOpen}
            onToggle={() => setTriageOpen((v) => !v)}
            emptyMessage="No items awaiting review. Upload or intake a new problem."
          >
            {triage.map((item) => (
              <BacklogCard
                key={item.id}
                item={item}
                selected={item.id === selectedId}
                onClick={() => onSelect(item.id)}
              />
            ))}
          </CollapsibleSection>

          <CollapsibleSection
            title="Live challenges"
            count={live.length}
            open={liveOpen}
            onToggle={() => setLiveOpen((v) => !v)}
            emptyMessage="Published challenges appear here after Approve & Publish."
          >
            {live.map((item) => (
              <BacklogCard
                key={item.id}
                item={item}
                selected={item.id === selectedId}
                onClick={() => onSelect(item.id)}
                compact
              />
            ))}
          </CollapsibleSection>

          <CollapsibleSection
            title="Closed"
            count={closed.length}
            open={closedOpen}
            onToggle={() => setClosedOpen((v) => !v)}
            emptyMessage="Close submissions on a live challenge to archive it here."
          >
            {closed.map((item) => (
              <BacklogCard
                key={item.id}
                item={item}
                selected={item.id === selectedId}
                onClick={() => onSelect(item.id)}
                compact
              />
            ))}
          </CollapsibleSection>
        </div>
      )}
    </aside>
  );
}
