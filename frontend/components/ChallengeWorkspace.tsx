"use client";

import dynamic from "next/dynamic";
import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";
import type { editor } from "monaco-editor";
import { api } from "@/lib/api";
import {
  loadLocalDraft,
  pickNewerDraft,
  saveLocalDraft,
  type SaveStatus,
} from "@/lib/draftStorage";
import type { SubmitResponse } from "@/lib/types";

const MonacoEditor = dynamic(() => import("@monaco-editor/react"), { ssr: false });

interface ChallengeWorkspaceProps {
  challengeId: string;
  onSubmitResult: (result: SubmitResponse) => void;
  onError: (message: string) => void;
  productMode?: boolean;
  externalLinks?: { figma?: string; deployment?: string };
  footer?: ReactNode;
  className?: string;
}

function monacoLanguage(path: string): string {
  if (path.endsWith(".py")) return "python";
  if (path.endsWith(".html")) return "html";
  if (path.endsWith(".css")) return "css";
  if (path.endsWith(".js") || path.endsWith(".tsx") || path.endsWith(".ts")) return "javascript";
  if (path.endsWith(".json")) return "json";
  return "markdown";
}

const SAVE_LABEL: Record<SaveStatus, string> = {
  idle: "",
  unsaved: "Unsaved changes",
  local: "Saved locally",
  saved: "Saved",
  offline: "Offline — saved locally",
  submitting: "Submitting…",
};

const OUTPUT_HEIGHT_DEFAULT = 96;
const OUTPUT_HEIGHT_MIN = 56;
const OUTPUT_HEIGHT_MAX = 480;

function sortedPaths(files: Record<string, string>): string[] {
  return Object.keys(files).sort();
}

export function ChallengeWorkspace({
  challengeId,
  onSubmitResult,
  onError,
  productMode = false,
  externalLinks,
  footer,
  className = "",
}: ChallengeWorkspaceProps) {
  const [files, setFiles] = useState<Record<string, string>>({});
  const [activeFile, setActiveFile] = useState<string>("");
  const [workspaceId, setWorkspaceId] = useState<string>("");
  const [revision, setRevision] = useState(0);
  const [saveStatus, setSaveStatus] = useState<SaveStatus>("idle");
  const [loading, setLoading] = useState(true);
  const [output, setOutput] = useState("$ sandbox ready\n");
  const [outputHeight, setOutputHeight] = useState(OUTPUT_HEIGHT_DEFAULT);
  const [running, setRunning] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const editorContainerRef = useRef<HTMLDivElement>(null);
  const workspaceBodyRef = useRef<HTMLDivElement>(null);
  const outputDragRef = useRef<{ startY: number; startHeight: number } | null>(null);
  const [editorHeight, setEditorHeight] = useState(400);
  const editorRef = useRef<editor.IStandaloneCodeEditor | null>(null);
  const monacoRef = useRef<typeof import("monaco-editor") | null>(null);
  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const validateTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const filesRef = useRef(files);
  const revisionRef = useRef(revision);
  const workspaceIdRef = useRef(workspaceId);

  filesRef.current = files;
  revisionRef.current = revision;
  workspaceIdRef.current = workspaceId;

  const applyMarkers = useCallback(
    (path: string, diagnostics: { line: number; column: number; message: string }[]) => {
      const editor = editorRef.current;
      const monaco = monacoRef.current;
      if (!editor || !monaco) return;
      const model = editor.getModel();
      if (!model) return;
      monaco.editor.setModelMarkers(
        model,
        "sandbox",
        diagnostics.map((d) => ({
          startLineNumber: d.line,
          startColumn: d.column,
          endLineNumber: d.line,
          endColumn: d.column + 1,
          message: d.message,
          severity: monaco.MarkerSeverity.Error,
        }))
      );
    },
    []
  );

  const persistDraft = useCallback(
    async (nextFiles: Record<string, string>, nextRevision: number) => {
      const wsId = workspaceIdRef.current;
      if (!wsId) return;

      const updatedAt = new Date().toISOString();
      await saveLocalDraft(challengeId, wsId, {
        files: nextFiles,
        updated_at: updatedAt,
        revision: nextRevision,
      });
      setSaveStatus("local");

      try {
        await api.saveDraft(challengeId, nextFiles, nextRevision, updatedAt);
        setSaveStatus("saved");
      } catch {
        setSaveStatus("offline");
      }
    },
    [challengeId]
  );

  const scheduleSave = useCallback(
    (nextFiles: Record<string, string>) => {
      setSaveStatus("unsaved");
      if (saveTimer.current) clearTimeout(saveTimer.current);
      saveTimer.current = setTimeout(() => {
        const nextRevision = revisionRef.current + 1;
        setRevision(nextRevision);
        void persistDraft(nextFiles, nextRevision);
      }, 2000);
    },
    [persistDraft]
  );

  const scheduleValidate = useCallback(
    (path: string, content: string) => {
      if (!path.endsWith(".py")) return;
      if (validateTimer.current) clearTimeout(validateTimer.current);
      validateTimer.current = setTimeout(() => {
        void api
          .validateFile(path, content)
          .then((res) => applyMarkers(path, res.diagnostics))
          .catch(() => {});
      }, 300);
    },
    [applyMarkers]
  );

  useEffect(() => {
    let cancelled = false;

    async function bootstrap() {
      try {
        const [boot, starter] = await Promise.all([
          api.bootstrapWorkspace(challengeId),
          api.getStarter(challengeId),
        ]);
        if (cancelled) return;

        setWorkspaceId(boot.workspace_id);

        const serverDraft = boot.draft
          ? {
              files: boot.draft.files,
              updated_at: boot.draft.updated_at,
              revision: boot.draft.client_revision,
            }
          : null;
        const localDraft = await loadLocalDraft(challengeId, boot.workspace_id);
        const chosen = pickNewerDraft(localDraft, serverDraft);
        const initialFiles = chosen?.files ?? starter.files;
        const paths = sortedPaths(initialFiles);

        setFiles(initialFiles);
        setActiveFile(paths[0] ?? "");
        setRevision(chosen?.revision ?? 0);
        setSaveStatus(chosen ? "saved" : "idle");
      } catch (e) {
        onError(e instanceof Error ? e.message : "Failed to load workspace");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    void bootstrap();
    return () => {
      cancelled = true;
    };
  }, [challengeId, onError]);

  useEffect(() => {
    const el = editorContainerRef.current;
    if (!el) return;

    const updateHeight = () => {
      const next = el.clientHeight;
      if (next > 0) setEditorHeight(next);
    };

    updateHeight();
    const observer = new ResizeObserver(updateHeight);
    observer.observe(el);
    return () => observer.disconnect();
  }, [loading, activeFile]);

  const clampOutputHeight = useCallback((height: number) => {
    const body = workspaceBodyRef.current;
    const maxFromBody = body ? Math.floor(body.clientHeight * 0.65) : OUTPUT_HEIGHT_MAX;
    const max = Math.min(OUTPUT_HEIGHT_MAX, Math.max(OUTPUT_HEIGHT_MIN, maxFromBody));
    return Math.min(max, Math.max(OUTPUT_HEIGHT_MIN, height));
  }, []);

  const handleOutputResizeStart = useCallback(
    (event: React.PointerEvent<HTMLDivElement>) => {
      event.preventDefault();
      outputDragRef.current = { startY: event.clientY, startHeight: outputHeight };
      event.currentTarget.setPointerCapture(event.pointerId);
    },
    [outputHeight]
  );

  const handleOutputResizeMove = useCallback(
    (event: React.PointerEvent<HTMLDivElement>) => {
      if (!outputDragRef.current) return;
      const delta = outputDragRef.current.startY - event.clientY;
      setOutputHeight(clampOutputHeight(outputDragRef.current.startHeight + delta));
    },
    [clampOutputHeight]
  );

  const handleOutputResizeEnd = useCallback((event: React.PointerEvent<HTMLDivElement>) => {
    if (!outputDragRef.current) return;
    outputDragRef.current = null;
    event.currentTarget.releasePointerCapture(event.pointerId);
  }, []);

  function updateFile(path: string, content: string) {
    setFiles((prev) => {
      const next = { ...prev, [path]: content };
      scheduleSave(next);
      scheduleValidate(path, content);
      return next;
    });
  }

  async function handleRun() {
    if (running) return;
    setRunning(true);
    setOutput((prev) => prev + "\n$ running public tests…\n");
    try {
      const { job_id } = await api.runPublicTests(challengeId, filesRef.current);
      let done = false;
      while (!done) {
        await new Promise((r) => setTimeout(r, 1000));
        const job = await api.getJob(job_id);
        if (job.status === "queued" || job.status === "running") continue;
        done = true;
        const chunk = [job.stdout, job.stderr].filter(Boolean).join("\n");
        setOutput(
          (prev) =>
            prev +
            chunk +
            `\n$ exit ${job.exit_code ?? "?"} (${job.status})\n`
        );
      }
    } catch (e) {
      setOutput((prev) => prev + `\n$ error: ${e instanceof Error ? e.message : "run failed"}\n`);
      onError(e instanceof Error ? e.message : "Run failed");
    } finally {
      setRunning(false);
    }
  }

  async function handleSubmit() {
    setSubmitting(true);
    setSaveStatus("submitting");
    setOutput((prev) => prev + "\n$ submitting solution…\n");
    try {
      const links: Record<string, string> = {};
      if (externalLinks?.figma?.trim()) links.figma = externalLinks.figma.trim();
      if (externalLinks?.deployment?.trim()) links.deployment = externalLinks.deployment.trim();

      const res = await api.submitSolution(
        challengeId,
        filesRef.current,
        productMode ? "html" : "python",
        Object.keys(links).length > 0 ? links : undefined
      );
      onSubmitResult(res);
      setSaveStatus("saved");
    } catch (e) {
      onError(e instanceof Error ? e.message : "Submit failed");
      setSaveStatus("unsaved");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleZipUpload(file: File) {
    setSubmitting(true);
    setSaveStatus("submitting");
    try {
      const buf = await file.arrayBuffer();
      const res = await api.submitZip(challengeId, buf);
      onSubmitResult(res);
      setSaveStatus("saved");
    } catch (e) {
      onError(e instanceof Error ? e.message : "ZIP submit failed");
      setSaveStatus("unsaved");
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return (
      <div className={`flex items-center justify-center h-full text-slate-500 text-sm ${className}`}>
        Loading workspace…
      </div>
    );
  }

  const paths = sortedPaths(files);

  return (
    <div
      className={`flex flex-col h-full min-h-0 overflow-hidden rounded-lg border border-surface-border bg-[#0a0a0c] ${className}`}
    >
      <div className="flex-shrink-0 flex items-center justify-between px-3 py-2 border-b border-surface-border bg-surface-raised">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-red-500/80" />
          <span className="w-2.5 h-2.5 rounded-full bg-yellow-500/80" />
          <span className="w-2.5 h-2.5 rounded-full bg-green-500/80" />
          <span className="text-[10px] text-slate-500 ml-2 uppercase tracking-widest">
            workspace — {productMode ? "prototype" : "python"}
          </span>
        </div>
        {saveStatus !== "idle" && (
          <span className="text-[10px] text-slate-500">{SAVE_LABEL[saveStatus]}</span>
        )}
      </div>

      <div ref={workspaceBodyRef} className="flex flex-1 min-h-0 overflow-hidden flex-col">
        <div className="flex flex-1 min-h-0 overflow-hidden">
          <aside className="w-48 flex-shrink-0 border-r border-surface-border overflow-y-auto bg-[#0d0d10]">
            {paths.map((path) => (
              <button
                key={path}
                type="button"
                onClick={() => setActiveFile(path)}
                className={`block w-full text-left px-3 py-1.5 text-xs font-mono truncate ${
                  activeFile === path
                    ? "bg-accent/20 text-accent"
                    : "text-slate-400 hover:bg-surface-muted"
                }`}
              >
                {path}
              </button>
            ))}
          </aside>

          <div ref={editorContainerRef} className="flex-1 min-w-0 min-h-0 overflow-hidden">
            {activeFile && editorHeight > 0 && (
              <MonacoEditor
                key={activeFile}
                height={editorHeight}
                language={monacoLanguage(activeFile)}
                theme="vs-dark"
                value={files[activeFile] ?? ""}
                onChange={(value) => updateFile(activeFile, value ?? "")}
                onMount={(editor, monaco) => {
                  editorRef.current = editor;
                  monacoRef.current = monaco;
                  const content = files[activeFile] ?? "";
                  scheduleValidate(activeFile, content);
                }}
                options={{
                  minimap: { enabled: false },
                  fontSize: 13,
                  scrollBeyondLastLine: false,
                  automaticLayout: true,
                }}
              />
            )}
          </div>
        </div>

        <div
          role="separator"
          aria-orientation="horizontal"
          aria-label="Resize terminal output"
          title="Drag to resize terminal"
          onPointerDown={handleOutputResizeStart}
          onPointerMove={handleOutputResizeMove}
          onPointerUp={handleOutputResizeEnd}
          onPointerCancel={handleOutputResizeEnd}
          className="group flex-shrink-0 h-2 cursor-row-resize touch-none select-none
            border-t border-surface-border bg-[#0a0a0c]
            hover:bg-accent/10 active:bg-accent/20"
        >
          <div className="mx-auto mt-0.5 h-0.5 w-10 rounded-full bg-surface-border group-hover:bg-accent/50" />
        </div>

        <pre
          style={{ height: outputHeight }}
          className="flex-shrink-0 overflow-y-auto p-3 text-xs text-slate-500 font-mono"
        >
          {output}
        </pre>
      </div>

      <div className="flex-shrink-0 border-t border-surface-border bg-surface-raised">
        {footer}
        <div className="flex flex-wrap gap-2 p-3">
        {!productMode && (
          <button
            type="button"
            onClick={() => void handleRun()}
            disabled={running || submitting}
            className="px-3 py-1.5 text-xs rounded border border-surface-border text-slate-300
              hover:bg-surface-muted disabled:opacity-50"
          >
            {running ? "Running…" : "Run Public Tests"}
          </button>
        )}
        <button
          type="button"
          onClick={() => void handleSubmit()}
          disabled={submitting || running || paths.length === 0}
          className="px-3 py-1.5 text-xs rounded bg-accent text-white font-semibold
            hover:bg-accent-dim disabled:opacity-50"
        >
          {submitting ? "Submitting…" : "Submit Project"}
        </button>
        <label className="px-3 py-1.5 text-xs rounded border border-surface-border text-slate-300
          hover:bg-surface-muted cursor-pointer disabled:opacity-50">
          Submit ZIP
          <input
            type="file"
            accept=".zip,application/zip"
            className="hidden"
            disabled={submitting || running}
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) void handleZipUpload(f);
              e.target.value = "";
            }}
          />
        </label>
        </div>
      </div>
    </div>
  );
}
