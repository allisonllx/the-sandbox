"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import type {
  BacklogItem,
  ChallengeReward,
  DomainObfuscationPreview,
  RelaxationConfig,
  RelaxedPreview,
  RewardType,
  ScopeCheckResponse,
} from "@/lib/types";
import { api } from "@/lib/api";
import { SensitivityBadge } from "./SensitivityBadge";

interface RelaxationPanelProps {
  item: BacklogItem;
  onPublished: (itemId: string) => void;
}

function Toggle({
  label,
  description,
  checked,
  onChange,
}: {
  label: string;
  description: string;
  checked: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <label className="flex items-start gap-3 cursor-pointer group">
      <div className="relative mt-0.5 flex-shrink-0">
        <input
          type="checkbox"
          className="sr-only"
          checked={checked}
          onChange={(e) => onChange(e.target.checked)}
        />
        <div
          className={`w-9 h-5 rounded-full border transition-colors duration-200 ${
            checked ? "bg-accent border-accent" : "bg-surface-muted border-surface-border"
          }`}
        />
        <div
          className={`absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white transition-transform duration-200 ${
            checked ? "translate-x-4" : "translate-x-0"
          }`}
        />
      </div>
      <div>
        <p className="text-sm text-slate-200 font-medium">{label}</p>
        <p className="text-[11px] text-slate-500 mt-0.5">{description}</p>
      </div>
    </label>
  );
}

function FieldDiff({ original, relaxed }: { original: string[]; relaxed: string[] }) {
  return (
    <div className="grid grid-cols-2 gap-3 text-[11px] font-mono">
      <div>
        <p className="text-slate-500 uppercase tracking-widest mb-2">Original</p>
        <div className="space-y-1">
          {original.map((f) => (
            <div key={f} className="text-slate-400 bg-surface-raised px-2 py-1 rounded">
              {f}
            </div>
          ))}
        </div>
      </div>
      <div>
        <p className="text-slate-500 uppercase tracking-widest mb-2">Relaxed</p>
        <div className="space-y-1">
          {relaxed.map((f, i) => (
            <div
              key={f}
              className={`px-2 py-1 rounded ${
                f !== original[i]
                  ? "text-green-400 bg-green-500/10 border border-green-500/20"
                  : "text-slate-400 bg-surface-raised"
              }`}
            >
              {f}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function DomainPreviewPanel({ preview }: { preview: DomainObfuscationPreview }) {
  const fieldEntries = preview.field_map ? Object.entries(preview.field_map) : [];
  const renamedFields = fieldEntries.filter(([orig, pub]) => orig !== pub);

  return (
    <div className="space-y-3 rounded-lg border border-purple-500/30 bg-purple-500/5 p-4">
      <p className="text-[11px] text-purple-400 uppercase tracking-widest font-semibold">
        Domain Obfuscation Preview (CTO only)
      </p>
      <div className="space-y-2 text-xs">
        <div>
          <p className="text-slate-500 text-[10px] uppercase">Internal intent</p>
          <p className="text-slate-400 italic">{preview.internal_intent}</p>
        </div>
        <div>
          <p className="text-slate-500 text-[10px] uppercase">Public title</p>
          <p className="text-slate-200 font-medium">{preview.public_title}</p>
        </div>
        <div>
          <p className="text-slate-500 text-[10px] uppercase">Public narrative</p>
          <p className="text-slate-300 leading-relaxed">{preview.public_narrative}</p>
        </div>
        {renamedFields.length > 0 && (
          <div>
            <p className="text-slate-500 text-[10px] uppercase mb-2">Column name remap</p>
            <div className="grid grid-cols-2 gap-2 text-[11px] font-mono">
              {renamedFields.map(([orig, pub]) => (
                <div key={orig} className="contents">
                  <div className="text-slate-500 bg-surface-raised px-2 py-1 rounded">{orig}</div>
                  <div className="text-purple-300 bg-purple-500/10 border border-purple-500/20 px-2 py-1 rounded">
                    {pub}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
        <p className="text-[10px] text-slate-500">{preview.transform_rationale}</p>
      </div>
    </div>
  );
}

export function RelaxationPanel({ item, onPublished }: RelaxationPanelProps) {
  const [config, setConfig] = useState<RelaxationConfig>({
    abstract_logic: false,
    synthesize_variables: false,
    noise_level: 0,
    abstract_brand: true,
    obfuscate_domain: item.id === "demo-005",
  });
  const [reward, setReward] = useState<ChallengeReward>(
    item.reward ?? {
      reward_type: "cash_bounty",
      amount_usd: 500,
      interview_benchmark: 75,
      locked: item.id === "demo-006",
    }
  );
  const [preview, setPreview] = useState<RelaxedPreview | null>(item.relaxed_preview);
  const [domainPreview, setDomainPreview] = useState<DomainObfuscationPreview | null>(
    item.domain_preview ?? null
  );
  const [scopeCheck, setScopeCheck] = useState<ScopeCheckResponse | null>(null);
  const [publishing, setPublishing] = useState(false);
  const [previewing, setPreviewing] = useState(false);
  const [published, setPublished] = useState(item.status === "published");
  const [microprd, setMicroprd] = useState(item.microprd);
  const [error, setError] = useState<string | null>(null);

  const noisePercent = Math.round(config.noise_level * 100);

  useEffect(() => {
    api
      .relax(item.id, config, reward, item.track ?? item.suggested_track ?? undefined)
      .then((res) => {
        setScopeCheck(res.scope_check ?? null);
      })
      .catch(() => {});
  }, [item.id]);

  async function handlePreview() {
    setPreviewing(true);
    setError(null);
    try {
      const res = await api.relax(item.id, config, reward, item.track ?? item.suggested_track ?? undefined);
      setPreview(res.preview);
      setDomainPreview(res.domain_preview ?? null);
      setScopeCheck(res.scope_check ?? null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Preview failed");
    } finally {
      setPreviewing(false);
    }
  }

  async function handlePublish() {
    setPublishing(true);
    setError(null);
    try {
      const res = await api.publish(item.id, config, reward, item.track ?? item.suggested_track ?? undefined);
      setMicroprd(res.microprd);
      setPublished(true);
      onPublished(item.id);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Publish failed";
      try {
        const parsed = JSON.parse(msg.replace(/^API \d+: /, "")) as { detail?: { message?: string; suggested_breakdown?: string[] } };
        const detail = parsed.detail;
        if (detail?.message) {
          setError(
            detail.suggested_breakdown?.length
              ? `${detail.message}\n\nSuggested breakdown:\n• ${detail.suggested_breakdown.join("\n• ")}`
              : detail.message
          );
        } else {
          setError(msg);
        }
      } catch {
        setError(msg);
      }
    } finally {
      setPublishing(false);
    }
  }

  const canPublish = scopeCheck?.allowed !== false && reward.locked;

  return (
    <div className="h-full flex flex-col gap-6 overflow-y-auto pr-1">
      <div className="space-y-2">
        <div className="flex items-center gap-3 flex-wrap">
          {item.tag && <SensitivityBadge tag={item.tag} />}
          {item.sponsor_profile && (
            <span className="text-[10px] text-amber-500/90 uppercase tracking-widest border border-amber-500/30 px-2 py-0.5 rounded">
              {item.sponsor_profile}
            </span>
          )}
          {item.pool_label && (
            <span className="text-[10px] text-slate-500 uppercase tracking-widest">
              {item.pool_label}
            </span>
          )}
        </div>
        <h2 className="text-lg font-semibold text-slate-100">
          {item.scores?.suggested_title ?? "Untitled Challenge"}
        </h2>
        <p className="text-xs text-slate-500">{item.source_label}</p>
        {scopeCheck && (
          <p
            className={`text-xs border-l-2 pl-3 ${
              scopeCheck.allowed ? "text-green-400/90 border-green-500/40" : "text-red-400 border-red-500/40"
            }`}
          >
            Scope: ~{scopeCheck.estimated_hours}h — {scopeCheck.reason}
          </p>
        )}
      </div>

      <hr className="border-surface-border" />

      <div className="space-y-5">
        <p className="text-xs text-slate-400 uppercase tracking-widest font-semibold">
          Relaxation Controls
        </p>
        <Toggle
          label="Abstract Proprietary Logic"
          description="Replace domain-specific field names with generic equivalents."
          checked={config.abstract_logic}
          onChange={(v) => setConfig((c) => ({ ...c, abstract_logic: v }))}
        />
        <Toggle
          label="Synthesize Variable Names"
          description="Map field names to deterministic abstract tokens."
          checked={config.synthesize_variables}
          onChange={(v) => setConfig((c) => ({ ...c, synthesize_variables: v }))}
        />
        <Toggle
          label="Obfuscate Industry Domain"
          description="Mask business intent (e.g. food delivery → equipment sharing) for stealth."
          checked={!!config.obfuscate_domain}
          onChange={(v) => setConfig((c) => ({ ...c, obfuscate_domain: v }))}
        />

        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <p className="text-sm text-slate-200 font-medium">Statistical Noise Level</p>
            <span className="text-sm font-semibold text-accent tabular-nums">{noisePercent}%</span>
          </div>
          <input
            type="range"
            min={0}
            max={100}
            value={noisePercent}
            onChange={(e) =>
              setConfig((c) => ({ ...c, noise_level: Number(e.target.value) / 100 }))
            }
            className="w-full accent-accent cursor-pointer"
          />
        </div>
      </div>

      <hr className="border-surface-border" />

      <div className="space-y-4">
        <p className="text-xs text-slate-400 uppercase tracking-widest font-semibold">
          Guaranteed Reward (demo)
        </p>
        <div className="flex gap-2">
          {(["cash_bounty", "interview_pass"] as RewardType[]).map((type) => (
            <button
              key={type}
              type="button"
              onClick={() => setReward((r) => ({ ...r, reward_type: type, locked: false }))}
              className={`text-xs px-3 py-1.5 rounded border ${
                reward.reward_type === type
                  ? "border-accent bg-accent/10 text-accent"
                  : "border-surface-border text-slate-500"
              }`}
            >
              {type === "cash_bounty" ? "Cash bounty" : "Interview pass"}
            </button>
          ))}
        </div>
        {reward.reward_type === "cash_bounty" ? (
          <label className="block text-xs text-slate-400">
            Amount (USD)
            <input
              type="number"
              value={reward.amount_usd ?? 500}
              onChange={(e) =>
                setReward((r) => ({ ...r, amount_usd: Number(e.target.value), locked: false }))
              }
              className="mt-1 w-full px-2 py-1.5 rounded border border-surface-border bg-surface text-slate-200"
            />
          </label>
        ) : (
          <label className="block text-xs text-slate-400">
            Score benchmark
            <input
              type="number"
              value={reward.interview_benchmark ?? 75}
              onChange={(e) =>
                setReward((r) => ({
                  ...r,
                  interview_benchmark: Number(e.target.value),
                  locked: false,
                }))
              }
              className="mt-1 w-full px-2 py-1.5 rounded border border-surface-border bg-surface text-slate-200"
            />
          </label>
        )}
        <button
          type="button"
          onClick={() => setReward((r) => ({ ...r, locked: true }))}
          className={`w-full py-2 text-xs rounded border ${
            reward.locked
              ? "border-green-500/40 bg-green-500/10 text-green-400"
              : "border-surface-border text-slate-400 hover:bg-surface-muted"
          }`}
        >
          {reward.locked ? "✓ Reward locked for publish" : "Lock reward (required to publish)"}
        </button>
      </div>

      <button
        onClick={() => void handlePreview()}
        disabled={previewing}
        className="w-full py-2 rounded-lg border border-surface-border text-sm text-slate-300
          hover:bg-surface-muted disabled:opacity-50"
      >
        {previewing ? "Generating preview…" : "Preview Changes"}
      </button>

      {preview && (
        <div className="space-y-3">
          <FieldDiff original={preview.original_fields} relaxed={preview.relaxed_fields} />
        </div>
      )}

      {domainPreview && <DomainPreviewPanel preview={domainPreview} />}

      {error && (
        <pre className="text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded px-3 py-2 whitespace-pre-wrap">
          {error}
        </pre>
      )}

      <hr className="border-surface-border" />

      {!published ? (
        <button
          onClick={() => void handlePublish()}
          disabled={publishing || !canPublish}
          className="w-full py-2.5 rounded-lg bg-accent hover:bg-accent-dim text-white text-sm font-semibold
            disabled:opacity-50"
        >
          {publishing ? "Generating Micro-PRD…" : "Approve & Publish Challenge →"}
        </button>
      ) : (
        <div className="space-y-4">
          <div className="flex items-center gap-2 text-green-400 text-sm font-semibold">
            <span>✓</span>
            <span>Challenge published</span>
          </div>
          <Link href={`/student/challenges/${item.id}`} className="text-xs text-accent hover:underline">
            Open student view →
          </Link>
          {microprd && (
            <p className="text-xs text-slate-400">{microprd.title}</p>
          )}
        </div>
      )}
    </div>
  );
}
