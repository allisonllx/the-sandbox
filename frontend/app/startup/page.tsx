"use client";

import { useEffect, useState, useCallback, Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import type { BacklogItem } from "@/lib/types";
import { api } from "@/lib/api";
import { BacklogSidebar } from "@/components/BacklogSidebar";
import { RelaxationPanel } from "@/components/RelaxationPanel";

const TRIAGE_STATUSES = new Set(["pending", "reviewing", "approved"]);

function defaultSelection(items: BacklogItem[], preferId?: string | null): string | null {
  if (preferId && items.some((i) => i.id === preferId)) {
    return preferId;
  }
  return (
    items.find((i) => TRIAGE_STATUSES.has(i.status))?.id ??
    items.find((i) => i.status === "published")?.id ??
    items.find((i) => i.status === "closed")?.id ??
    null
  );
}

function StartupDashboardInner() {
  const searchParams = useSearchParams();
  const selectFromUrl = searchParams.get("select");

  const [items, setItems] = useState<BacklogItem[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const selectedItem = items.find((i) => i.id === selectedId) ?? null;
  const triageCount = items.filter((i) => TRIAGE_STATUSES.has(i.status)).length;
  const liveCount = items.filter((i) => i.status === "published").length;
  const closedCount = items.filter((i) => i.status === "closed").length;

  const loadBacklog = useCallback(async (preferId?: string | null) => {
    try {
      const data = await api.getBacklog();
      setItems(data);
      setSelectedId((prev) => {
        if (preferId && data.some((i) => i.id === preferId)) {
          return preferId;
        }
        if (prev && data.some((i) => i.id === prev)) {
          return prev;
        }
        return defaultSelection(data);
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load backlog");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadBacklog(selectFromUrl);
  }, [loadBacklog, selectFromUrl]);

  function handleIntake(item: BacklogItem) {
    setItems((prev) => {
      const rest = prev.filter((i) => i.id !== item.id);
      return [item, ...rest];
    });
    setSelectedId(item.id);
  }

  function handlePublished(itemId: string) {
    setItems((prev) =>
      prev.map((i) => (i.id === itemId ? { ...i, status: "published" } : i))
    );
  }

  function handleClosed(itemId: string) {
    setItems((prev) =>
      prev.map((i) => (i.id === itemId ? { ...i, status: "closed" } : i))
    );
  }

  return (
    <div className="flex flex-col h-screen overflow-hidden">
      <header className="flex-shrink-0 border-b border-surface-border bg-surface-raised px-6 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-accent font-semibold text-sm tracking-wider">SANDBOX</span>
            <span className="text-surface-border">|</span>
            <span className="text-slate-400 text-xs uppercase tracking-widest">CTO Dashboard</span>
          </div>
          <div className="flex items-center gap-4 text-[11px] text-slate-500">
            <Link href="/startup/upload" className="text-accent/90 hover:text-accent">
              + Upload
            </Link>
            <span>
              {triageCount} in triage · {liveCount} live · {closedCount} closed
            </span>
            {selectedItem &&
              (selectedItem.status === "published" || selectedItem.status === "closed") && (
                <Link
                  href={`/startup/matches/${selectedItem.id}`}
                  className="text-amber-400/90 hover:text-amber-400"
                >
                  Match Radar
                </Link>
              )}
            <span className="w-2 h-2 rounded-full bg-green-500 inline-block" />
            <span>Privacy Proxy Active</span>
          </div>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden min-h-0">
        <BacklogSidebar
          items={items}
          selectedId={selectedId}
          loading={loading}
          error={error}
          onSelect={setSelectedId}
          onIntake={handleIntake}
        />

        <main className="flex-1 overflow-y-auto bg-surface min-h-0">
          {selectedItem ? (
            <div className="max-w-2xl mx-auto px-8 py-6">
              <RelaxationPanel
                key={selectedItem.id}
                item={selectedItem}
                onPublished={handlePublished}
                onClosed={handleClosed}
              />
            </div>
          ) : (
            !loading && (
              <div className="flex items-center justify-center h-full text-slate-600 text-sm">
                Select a backlog item to review
              </div>
            )
          )}
        </main>
      </div>
    </div>
  );
}

export default function StartupDashboard() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-surface flex items-center justify-center text-slate-600 text-sm">
          Loading backlog…
        </div>
      }
    >
      <StartupDashboardInner />
    </Suspense>
  );
}
