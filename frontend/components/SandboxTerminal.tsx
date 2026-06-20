"use client";

import { useState } from "react";

interface SandboxTerminalProps {
  challengeId: string;
  onSubmit: (code: string) => Promise<void>;
  submitting: boolean;
}

export function SandboxTerminal({ challengeId, onSubmit, submitting }: SandboxTerminalProps) {
  const [code, setCode] = useState(
    `# Challenge: ${challengeId}\n# Write your solution below\n\ndef solve():\n    pass\n\nif __name__ == "__main__":\n    solve()\n`
  );
  const [output, setOutput] = useState<string>("$ sandbox ready — edit code and click Run or Submit\n");

  function handleRun() {
    setOutput(
      (prev) =>
        prev +
        `\n$ python solution.py\n[mock] Syntax OK — ${code.split("\n").length} lines loaded\n[mock] Run full tests via Submit\n`
    );
  }

  async function handleSubmit() {
    setOutput((prev) => prev + "\n$ submitting solution...\n");
    await onSubmit(code);
  }

  return (
    <div className="flex flex-col h-full min-h-[420px] rounded-lg border border-surface-border overflow-hidden bg-[#0a0a0c]">
      <div className="flex items-center gap-2 px-3 py-2 border-b border-surface-border bg-surface-raised">
        <span className="w-2.5 h-2.5 rounded-full bg-red-500/80" />
        <span className="w-2.5 h-2.5 rounded-full bg-yellow-500/80" />
        <span className="w-2.5 h-2.5 rounded-full bg-green-500/80" />
        <span className="text-[10px] text-slate-500 ml-2 uppercase tracking-widest">
          sandbox — python
        </span>
      </div>

      <textarea
        value={code}
        onChange={(e) => setCode(e.target.value)}
        spellCheck={false}
        className="flex-1 w-full p-4 bg-transparent text-sm text-green-400 font-mono resize-none
          focus:outline-none min-h-[200px]"
      />

      <pre className="h-24 overflow-auto p-3 text-xs text-slate-500 border-t border-surface-border font-mono">
        {output}
      </pre>

      <div className="flex gap-2 p-3 border-t border-surface-border bg-surface-raised">
        <button
          type="button"
          onClick={handleRun}
          className="px-3 py-1.5 text-xs rounded border border-surface-border text-slate-300
            hover:bg-surface-muted"
        >
          Run
        </button>
        <button
          type="button"
          onClick={handleSubmit}
          disabled={submitting || !code.trim()}
          className="px-3 py-1.5 text-xs rounded bg-accent text-white font-semibold
            hover:bg-accent-dim disabled:opacity-50"
        >
          {submitting ? "Submitting…" : "Submit Solution"}
        </button>
      </div>
    </div>
  );
}
