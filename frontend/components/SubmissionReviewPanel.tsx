"use client";

import dynamic from "next/dynamic";
import { useMemo, useState } from "react";

const MonacoEditor = dynamic(() => import("@monaco-editor/react"), { ssr: false });

function monacoLanguage(path: string): string {
  if (path.endsWith(".py")) return "python";
  if (path.endsWith(".html")) return "html";
  if (path.endsWith(".css")) return "css";
  if (path.endsWith(".js") || path.endsWith(".tsx") || path.endsWith(".ts")) return "javascript";
  if (path.endsWith(".json")) return "json";
  return "markdown";
}

export function SubmissionReviewPanel({
  files,
}: {
  files: Record<string, string>;
}) {
  const paths = useMemo(() => Object.keys(files).sort(), [files]);
  const [activeFile, setActiveFile] = useState(paths[0] ?? "");

  const current = activeFile && files[activeFile] != null ? activeFile : paths[0] ?? "";

  if (paths.length === 0) {
    return (
      <p className="text-sm text-slate-500 border border-dashed border-surface-border rounded-lg p-6">
        No files in this submission snapshot.
      </p>
    );
  }

  return (
    <div className="flex border border-surface-border rounded-lg overflow-hidden min-h-[420px] bg-surface-raised">
      <aside className="w-48 flex-shrink-0 border-r border-surface-border bg-surface overflow-y-auto">
        <p className="text-[10px] uppercase tracking-widest text-slate-500 px-3 py-2 border-b border-surface-border">
          Submitted files
        </p>
        <ul className="py-1">
          {paths.map((path) => (
            <li key={path}>
              <button
                type="button"
                onClick={() => setActiveFile(path)}
                className={`w-full text-left px-3 py-1.5 text-[11px] font-mono truncate ${
                  path === current
                    ? "bg-accent/15 text-accent"
                    : "text-slate-400 hover:bg-surface-muted/50"
                }`}
              >
                {path}
              </button>
            </li>
          ))}
        </ul>
      </aside>
      <div className="flex-1 min-w-0">
        {current && (
          <MonacoEditor
            height="420px"
            language={monacoLanguage(current)}
            value={files[current] ?? ""}
            theme="vs-dark"
            options={{
              readOnly: true,
              minimap: { enabled: false },
              fontSize: 13,
              fontFamily: "JetBrains Mono, monospace",
              scrollBeyondLastLine: false,
              wordWrap: "on",
            }}
          />
        )}
      </div>
    </div>
  );
}
