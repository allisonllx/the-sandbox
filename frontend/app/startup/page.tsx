"use client";

import { useEffect, useState, useCallback, Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import type { BacklogItem } from "@/lib/types";
import { api } from "@/lib/api";
import { BacklogCard } from "@/components/BacklogCard";
import { FounderIntakePanel } from "@/components/FounderIntakePanel";
import { RelaxationPanel } from "@/components/RelaxationPanel";

function StartupDashboardInner() {
  const searchParams = useSearchParams();
  const selectFromUrl = searchParams.get("select");

  const [items, setItems] = useState<BacklogItem[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const selectedItem = items.find((i) => i.id === selectedId) ?? null;

  const loadBacklog = useCallback(async (preferId?: string | null) => {
    try {
      const data = await api.getBacklog();
      setItems(data);
      const pick =
        preferId && data.some((i) => i.id === preferId)
          ? preferId
          : data.length > 0
            ? data[0].id
            : null;
      setSelectedId((prev) => pick ?? prev);
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

  return (
    <div className="flex flex-col h-screen overflow-hidden">
      {/* Top bar */}
      <header className="flex-shrink-0 border-b border-surface-border bg-surface-raised px-6 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-accent font-semibold text-sm tracking-wider">SANDBOX</span>
            <span className="text-surface-border">|</span>
            <span className="text-slate-400 text-xs uppercase tracking-widest">CTO Dashboard</span>
          </div>
          <div className="flex items-center gap-4 text-[11px] text-slate-500">
            <Link
              href="/startup/upload"
              className="text-accent/90 hover:text-accent"
            >
              + Upload
            </Link>
            <span>{items.length} items in backlog</span>
            {selectedItem?.status === "published" && (
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

      {/* Main split panel */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left — backlog list */}
        <aside className="w-80 flex-shrink-0 border-r border-surface-border bg-surface overflow-y-auto">
          <div className="px-4 py-3 border-b border-surface-border">
            <p className="text-[11px] text-slate-500 uppercase tracking-widest">
              Prioritised Backlog
            </p>
          </div>

          <div className="p-3 space-y-2">
            <FounderIntakePanel onIntake={handleIntake} />
            {loading && (
              <div className="text-center py-12 text-slate-600 text-sm">Loading…</div>
            )}
            {error && (
              <div className="text-center py-8 text-red-400 text-xs bg-red-500/10 border border-red-500/20 rounded-lg p-4">
                {error}
                <br />
                <span className="text-slate-500 mt-1 block">
                  Is the backend running on :8000?
                </span>
              </div>
            )}
            {!loading &&
              !error &&
              items.map((item) => (
                <BacklogCard
                  key={item.id}
                  item={item}
                  selected={item.id === selectedId}
                  onClick={() => setSelectedId(item.id)}
                />
              ))}
          </div>
        </aside>

        {/* Right — relaxation controls */}
        <main className="flex-1 overflow-y-auto bg-surface">
          {selectedItem ? (
            <div className="max-w-2xl mx-auto px-8 py-6">
              <RelaxationPanel
                key={selectedItem.id}
                item={selectedItem}
                onPublished={handlePublished}
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
