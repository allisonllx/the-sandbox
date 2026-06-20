"use client";

import { useState } from "react";
import Link from "next/link";
import type { BacklogItem, RelaxationConfig, RelaxedPreview } from "@/lib/types";
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

function FieldDiff({
  original,
  relaxed,
}: {
  original: string[];
  relaxed: string[];
}) {
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

export function RelaxationPanel({ item, onPublished }: RelaxationPanelProps) {
  const [config, setConfig] = useState<RelaxationConfig>({
    abstract_logic: false,
    synthesize_variables: false,
    noise_level: 0,
  });
  const [preview, setPreview] = useState<RelaxedPreview | null>(item.relaxed_preview);
  const [publishing, setPublishing] = useState(false);
  const [previewing, setPreviewing] = useState(false);
  const [published, setPublished] = useState(item.status === "published");
  const [microprd, setMicroprd] = useState(item.microprd);
  const [error, setError] = useState<string | null>(null);

  const noisePercent = Math.round(config.noise_level * 100);

  async function handlePreview() {
    setPreviewing(true);
    setError(null);
    try {
      const res = await api.relax(item.id, config);
      setPreview(res.preview);
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
      const res = await api.publish(item.id, config);
      setMicroprd(res.microprd);
      setPublished(true);
      onPublished(item.id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Publish failed");
    } finally {
      setPublishing(false);
    }
  }

  return (
    <div className="h-full flex flex-col gap-6 overflow-y-auto pr-1">
      {/* Header */}
      <div className="space-y-2">
        <div className="flex items-center gap-3">
          {item.tag && <SensitivityBadge tag={item.tag} />}
          <span className="text-[11px] text-slate-500 uppercase tracking-widest">
            {item.metadata.fields.length} fields · {item.metadata.approximate_row_scale?.toLocaleString()} rows
          </span>
        </div>
        <h2 className="text-lg font-semibold text-slate-100">
          {item.scores?.suggested_title ?? "Untitled Challenge"}
        </h2>
        <p className="text-xs text-slate-500">{item.source_label}</p>
        {item.scores && (
          <p className="text-xs text-slate-400 italic border-l-2 border-surface-muted pl-3">
            {item.scores.sensitivity_reason}
          </p>
        )}
      </div>

      <hr className="border-surface-border" />

      {/* Relaxation controls */}
      <div className="space-y-5">
        <p className="text-xs text-slate-400 uppercase tracking-widest font-semibold">
          Relaxation Controls
        </p>

        <Toggle
          label="Abstract Proprietary Logic"
          description="Replace domain-specific field names (payment, auth, salary) with generic equivalents."
          checked={config.abstract_logic}
          onChange={(v) => setConfig((c) => ({ ...c, abstract_logic: v }))}
        />
        <Toggle
          label="Synthesize Variable Names"
          description="Map all field names to deterministic abstract tokens (e.g. node_alpha, stream_delta)."
          checked={config.synthesize_variables}
          onChange={(v) => setConfig((c) => ({ ...c, synthesize_variables: v }))}
        />

        {/* Noise slider */}
        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <div>
              <p className="text-sm text-slate-200 font-medium">Statistical Noise Level</p>
              <p className="text-[11px] text-slate-500 mt-0.5">
                Perturbs row counts and event frequencies while preserving structural shape.
              </p>
            </div>
            <span className="text-sm font-semibold text-accent tabular-nums w-10 text-right">
              {noisePercent}%
            </span>
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
          <div className="flex justify-between text-[10px] text-slate-600">
            <span>No noise</span>
            <span>Max noise</span>
          </div>
        </div>
      </div>

      {/* Preview button */}
      <button
        onClick={handlePreview}
        disabled={previewing}
        className="w-full py-2 rounded-lg border border-surface-border text-sm text-slate-300
          hover:bg-surface-muted hover:border-slate-500 transition-colors disabled:opacity-50"
      >
        {previewing ? "Generating preview…" : "Preview Changes"}
      </button>

      {/* Field diff */}
      {preview && (
        <div className="space-y-3">
          <p className="text-[11px] text-slate-500 uppercase tracking-widest font-semibold">
            Field Name Preview
          </p>
          <FieldDiff original={preview.original_fields} relaxed={preview.relaxed_fields} />
          {preview.original_row_scale !== preview.relaxed_row_scale && (
            <p className="text-xs text-slate-400">
              Row scale:{" "}
              <span className="line-through text-slate-600">{preview.original_row_scale?.toLocaleString()}</span>
              {" → "}
              <span className="text-green-400">{preview.relaxed_row_scale?.toLocaleString()}</span>
            </p>
          )}
        </div>
      )}

      {error && (
        <p className="text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded px-3 py-2">
          {error}
        </p>
      )}

      <hr className="border-surface-border" />

      {/* Approve & Publish */}
      {!published ? (
        <button
          onClick={handlePublish}
          disabled={publishing}
          className="w-full py-2.5 rounded-lg bg-accent hover:bg-accent-dim text-white text-sm font-semibold
            transition-colors disabled:opacity-50"
        >
          {publishing ? "Generating Micro-PRD…" : "Approve & Publish Challenge →"}
        </button>
      ) : (
        <div className="space-y-4">
          <div className="flex items-center gap-2 text-green-400 text-sm font-semibold">
            <span>✓</span>
            <span>Challenge published to public sandbox</span>
          </div>
          <Link
            href={`/student/challenges/${item.id}`}
            className="inline-block text-xs text-accent hover:underline"
          >
            Open student view →
          </Link>

          {microprd && (
            <div className="space-y-3 text-xs">
              <p className="text-slate-400 uppercase tracking-widest font-semibold">Micro-PRD</p>
              <div className="bg-surface-raised border border-surface-border rounded-lg p-4 space-y-4">
                <p className="text-slate-100 font-semibold">{microprd.title}</p>
                <div>
                  <p className="text-slate-500 uppercase tracking-wider text-[10px] mb-1">Context</p>
                  <p className="text-slate-300 leading-relaxed">{microprd.context}</p>
                </div>
                <div>
                  <p className="text-slate-500 uppercase tracking-wider text-[10px] mb-1">Definition of Success</p>
                  <ul className="space-y-1">
                    {microprd.definition_of_success.map((s, i) => (
                      <li key={i} className="text-slate-300 flex gap-2">
                        <span className="text-accent flex-shrink-0">›</span>
                        {s}
                      </li>
                    ))}
                  </ul>
                </div>
                <div>
                  <p className="text-slate-500 uppercase tracking-wider text-[10px] mb-1">Constraints</p>
                  <ul className="space-y-1">
                    {microprd.structural_constraints.map((c, i) => (
                      <li key={i} className="text-slate-400 flex gap-2">
                        <span className="text-slate-600 flex-shrink-0">—</span>
                        {c}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
