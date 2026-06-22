"use client";

import { useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import type { InputFormat } from "@/lib/types";
import {
  MAX_UPLOAD_BYTES,
  MAX_UPLOAD_CHARS,
  savePendingUpload,
  type PendingUpload,
} from "@/lib/uploadSession";

type UploadKind = "description" | "logs";

const KIND_OPTIONS: { id: UploadKind; label: string; hint: string; format: InputFormat }[] = [
  {
    id: "description",
    label: "Task description",
    hint: "Internal problem brief in plain language — not raw logs.",
    format: "text",
  },
  {
    id: "logs",
    label: "Log file or paste",
    hint: "Paste log lines or upload a .log / .txt file. PII is stripped locally before scoring.",
    format: "log",
  },
];

async function readFileAsText(file: File): Promise<string> {
  if (file.size > MAX_UPLOAD_BYTES) {
    throw new Error(`File too large (max ${Math.round(MAX_UPLOAD_BYTES / 1024)} KB).`);
  }
  return file.text();
}

export default function StartupUploadPage() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [kind, setKind] = useState<UploadKind>("description");
  const [label, setLabel] = useState("");
  const [content, setContent] = useState("");
  const [fileName, setFileName] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const selected = KIND_OPTIONS.find((k) => k.id === kind)!;

  async function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setError(null);
    try {
      const text = await readFileAsText(file);
      if (text.length > MAX_UPLOAD_CHARS) {
        throw new Error(`Content exceeds ${MAX_UPLOAD_CHARS.toLocaleString()} character limit.`);
      }
      setContent(text);
      setFileName(file.name);
      if (!label.trim()) {
        setLabel(file.name.replace(/\.[^.]+$/, ""));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to read file");
    }
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    const trimmed = content.trim();
    if (!trimmed) {
      setError("Add a task description or log content before continuing.");
      return;
    }
    if (trimmed.length > MAX_UPLOAD_CHARS) {
      setError(`Content exceeds ${MAX_UPLOAD_CHARS.toLocaleString()} characters.`);
      return;
    }

    const payload: PendingUpload = {
      content: trimmed,
      sourceLabel: label.trim() || (kind === "logs" ? "Uploaded logs" : "Founder brief"),
      format: selected.format,
      kind,
      fileName: fileName ?? undefined,
    };
    savePendingUpload(payload);
    router.push("/startup/upload/loading");
  }

  return (
    <div className="min-h-screen bg-surface flex flex-col">
      <header className="border-b border-surface-border bg-surface-raised px-6 py-3">
        <div className="max-w-2xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link href="/startup" className="text-slate-500 hover:text-slate-300 text-xs">
              ← Backlog
            </Link>
            <span className="text-surface-border">|</span>
            <span className="text-slate-400 text-xs uppercase tracking-widest">Add to backlog</span>
          </div>
          <span className="text-[10px] text-green-500/90">Privacy proxy local</span>
        </div>
      </header>

      <main className="flex-1 max-w-2xl mx-auto w-full px-6 py-8">
        <h1 className="text-lg text-slate-200 font-medium mb-1">Upload internal context</h1>
        <p className="text-sm text-slate-500 mb-6 leading-relaxed">
          Raw content is sanitized on the server in-process — only structural metadata is scored.
          Nothing is sent to external LLMs until you preview and publish a challenge.
        </p>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="flex gap-2">
            {KIND_OPTIONS.map((opt) => (
              <button
                key={opt.id}
                type="button"
                onClick={() => {
                  setKind(opt.id);
                  setFileName(null);
                }}
                className={`flex-1 text-xs py-2.5 px-3 rounded-lg border transition-colors ${
                  kind === opt.id
                    ? "border-accent/50 bg-accent/10 text-accent"
                    : "border-surface-border text-slate-400 hover:border-slate-600"
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>

          <p className="text-[11px] text-slate-500">{selected.hint}</p>

          <div>
            <label className="block text-[11px] uppercase tracking-widest text-slate-500 mb-1.5">
              Source label
            </label>
            <input
              type="text"
              value={label}
              onChange={(e) => setLabel(e.target.value)}
              placeholder={kind === "logs" ? "e.g. Datadog APM alerts — March 2024" : "e.g. Payment retry storm"}
              className="w-full text-sm px-3 py-2 rounded-lg border border-surface-border bg-surface-raised text-slate-200"
            />
          </div>

          {kind === "logs" && (
            <div>
              <label className="block text-[11px] uppercase tracking-widest text-slate-500 mb-1.5">
                Log file
              </label>
              <input
                ref={fileInputRef}
                type="file"
                accept=".log,.txt,.csv,.json,text/plain"
                onChange={handleFileChange}
                className="block w-full text-xs text-slate-400 file:mr-3 file:py-2 file:px-3 file:rounded file:border-0 file:bg-surface-border file:text-slate-300"
              />
              {fileName && (
                <p className="text-[10px] text-slate-500 mt-1">Loaded: {fileName}</p>
              )}
            </div>
          )}

          <div>
            <label className="block text-[11px] uppercase tracking-widest text-slate-500 mb-1.5">
              {kind === "logs" ? "Log content" : "Problem description"}
            </label>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              rows={12}
              placeholder={
                kind === "logs"
                  ? "2024-03-12 ERROR payment retry_count=3 gateway_response_code=502 ..."
                  : "Our webhook retries duplicate charges when the gateway returns 502. We need idempotent retry handling."
              }
              className="w-full text-sm px-3 py-2 rounded-lg border border-surface-border bg-surface-raised text-slate-200 font-mono text-[13px] leading-relaxed resize-y min-h-[200px]"
            />
            <p className="text-[10px] text-slate-600 mt-1 text-right">
              {content.length.toLocaleString()} / {MAX_UPLOAD_CHARS.toLocaleString()}
            </p>
          </div>

          {error && (
            <div className="text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">
              {error}
            </div>
          )}

          <div className="rounded-lg border border-surface-border bg-surface-raised/50 px-3 py-2 text-[11px] text-slate-500 leading-relaxed">
            <strong className="text-slate-400 font-normal">API path:</strong>{" "}
            <code className="text-accent/90">POST /proxy/sanitize</code> →{" "}
            <code className="text-accent/90">POST /triage/score</code>
            <span className="block mt-1">
              (Or one call via <code className="text-accent/90">POST /triage/intake</code> — same pipeline.)
            </span>
          </div>

          <button
            type="submit"
            disabled={!content.trim()}
            className="w-full py-2.5 rounded-lg bg-accent/20 text-accent hover:bg-accent/30 disabled:opacity-40 text-sm font-medium"
          >
            Sanitize &amp; add to backlog
          </button>
        </form>
      </main>
    </div>
  );
}
