"use client";

import { useState } from "react";
import { ChallengeWorkspace } from "@/components/ChallengeWorkspace";
import type { SubmitResponse } from "@/lib/types";

interface ProductWorkspaceProps {
  challengeId: string;
  onSubmitResult: (result: SubmitResponse) => void;
  onError: (message: string) => void;
}

function ExternalLinksPanel({
  figmaUrl,
  deploymentUrl,
  onFigmaChange,
  onDeploymentChange,
}: {
  figmaUrl: string;
  deploymentUrl: string;
  onFigmaChange: (value: string) => void;
  onDeploymentChange: (value: string) => void;
}) {
  return (
    <div className="px-3 pt-3 pb-2 space-y-2 border-b border-surface-border">
      <p className="text-[10px] uppercase tracking-widest text-slate-500 font-semibold">
        External Links (optional)
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        <label className="block space-y-1 min-w-0">
          <span className="text-[10px] text-slate-500">Figma prototype URL</span>
          <input
            type="url"
            value={figmaUrl}
            onChange={(e) => onFigmaChange(e.target.value)}
            placeholder="https://figma.com/file/..."
            className="w-full text-xs px-2 py-1.5 rounded border border-surface-border bg-surface
              text-slate-200 placeholder:text-slate-600"
          />
        </label>
        <label className="block space-y-1 min-w-0">
          <span className="text-[10px] text-slate-500">Deployed preview URL</span>
          <input
            type="url"
            value={deploymentUrl}
            onChange={(e) => onDeploymentChange(e.target.value)}
            placeholder="https://your-preview.example.com"
            className="w-full text-xs px-2 py-1.5 rounded border border-surface-border bg-surface
              text-slate-200 placeholder:text-slate-600"
          />
        </label>
      </div>
    </div>
  );
}

export function ProductWorkspace({
  challengeId,
  onSubmitResult,
  onError,
}: ProductWorkspaceProps) {
  const [figmaUrl, setFigmaUrl] = useState("");
  const [deploymentUrl, setDeploymentUrl] = useState("");

  return (
    <ChallengeWorkspace
      challengeId={challengeId}
      productMode
      className="h-full"
      externalLinks={{
        figma: figmaUrl,
        deployment: deploymentUrl,
      }}
      footer={
        <ExternalLinksPanel
          figmaUrl={figmaUrl}
          deploymentUrl={deploymentUrl}
          onFigmaChange={setFigmaUrl}
          onDeploymentChange={setDeploymentUrl}
        />
      }
      onSubmitResult={onSubmitResult}
      onError={onError}
    />
  );
}
