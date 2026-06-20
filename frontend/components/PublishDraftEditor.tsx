"use client";

import type { ChallengeTrack, CompanyTechProfile, PublishDraft } from "@/lib/types";

function EditableList({
  label,
  items,
  onChange,
  placeholder = "Add item…",
}: {
  label: string;
  items: string[];
  onChange: (items: string[]) => void;
  placeholder?: string;
}) {
  return (
    <div className="space-y-2">
      <p className="text-[10px] text-slate-500 uppercase tracking-widest">{label}</p>
      <div className="space-y-1.5">
        {items.map((item, i) => (
          <div key={i} className="flex gap-2">
            <input
              type="text"
              value={item}
              onChange={(e) => {
                const next = [...items];
                next[i] = e.target.value;
                onChange(next);
              }}
              className="flex-1 text-xs px-2 py-1.5 rounded border border-surface-border bg-surface text-slate-200"
            />
            <button
              type="button"
              onClick={() => onChange(items.filter((_, j) => j !== i))}
              className="text-xs px-2 text-slate-500 hover:text-red-400"
              aria-label="Remove"
            >
              ×
            </button>
          </div>
        ))}
      </div>
      <button
        type="button"
        onClick={() => onChange([...items, ""])}
        className="text-xs text-accent hover:underline"
      >
        + Add {label.toLowerCase()}
      </button>
      {items.length === 0 && (
        <input
          type="text"
          placeholder={placeholder}
          onKeyDown={(e) => {
            if (e.key === "Enter" && e.currentTarget.value.trim()) {
              onChange([e.currentTarget.value.trim()]);
              e.currentTarget.value = "";
            }
          }}
          className="w-full text-xs px-2 py-1.5 rounded border border-dashed border-surface-border bg-surface text-slate-400"
        />
      )}
    </div>
  );
}

const STAGE_OPTIONS = ["Seed", "Series A", "Series B", "Growth"];
const TEAM_OPTIONS = ["1-10", "11-50", "51-200", "201-500"];

export function PublishDraftEditor({
  draft,
  track,
  onChange,
}: {
  draft: PublishDraft;
  track: ChallengeTrack;
  onChange: (draft: PublishDraft) => void;
}) {
  const isProduct = track === "product_feature";

  function patch(partial: Partial<PublishDraft>) {
    onChange({ ...draft, ...partial });
  }

  function patchProfile(partial: Partial<CompanyTechProfile>) {
    patch({ company_profile: { ...draft.company_profile, ...partial } });
  }

  function patchStack(text: string) {
    patchProfile({
      tech_stack: text
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean),
    });
  }

  return (
    <div className="space-y-4 rounded-lg border border-accent/30 bg-accent/5 p-4">
      <div>
        <p className="text-[11px] text-accent uppercase tracking-widest font-semibold">
          Edit Student Release Preview
        </p>
        <p className="text-[10px] text-slate-500 mt-1">
          Refine the problem statement, success criteria, and company profile before publish.
        </p>
      </div>

      <label className="block space-y-1">
        <span className="text-[10px] text-slate-500 uppercase tracking-widest">Challenge title</span>
        <input
          type="text"
          value={draft.title}
          onChange={(e) => patch({ title: e.target.value })}
          className="w-full text-sm px-2 py-1.5 rounded border border-surface-border bg-surface text-slate-100"
        />
      </label>

      <label className="block space-y-1">
        <span className="text-[10px] text-slate-500 uppercase tracking-widest">Problem statement (context)</span>
        <textarea
          value={draft.context}
          onChange={(e) => patch({ context: e.target.value })}
          rows={4}
          className="w-full text-xs px-2 py-1.5 rounded border border-surface-border bg-surface text-slate-200 leading-relaxed"
        />
      </label>

      <EditableList
        label="Definition of success"
        items={draft.definition_of_success}
        onChange={(definition_of_success) => patch({ definition_of_success })}
        placeholder="First success criterion…"
      />

      <EditableList
        label="Evaluation focus"
        items={draft.evaluation_focus}
        onChange={(evaluation_focus) => patch({ evaluation_focus })}
      />

      <EditableList
        label="Structural constraints"
        items={draft.structural_constraints}
        onChange={(structural_constraints) => patch({ structural_constraints })}
      />

      {isProduct && (
        <>
          <label className="block space-y-1">
            <span className="text-[10px] text-slate-500 uppercase tracking-widest">User persona</span>
            <textarea
              value={draft.user_persona ?? ""}
              onChange={(e) => patch({ user_persona: e.target.value })}
              rows={2}
              className="w-full text-xs px-2 py-1.5 rounded border border-surface-border bg-surface text-slate-200"
            />
          </label>
          <label className="block space-y-1">
            <span className="text-[10px] text-slate-500 uppercase tracking-widest">Problem framing</span>
            <textarea
              value={draft.problem_framing ?? ""}
              onChange={(e) => patch({ problem_framing: e.target.value })}
              rows={2}
              className="w-full text-xs px-2 py-1.5 rounded border border-surface-border bg-surface text-slate-200"
            />
          </label>
          <EditableList
            label="Design considerations"
            items={draft.design_considerations ?? []}
            onChange={(design_considerations) => patch({ design_considerations })}
          />
          <EditableList
            label="Deliverable requirements"
            items={draft.deliverable_requirements ?? []}
            onChange={(deliverable_requirements) => patch({ deliverable_requirements })}
          />
        </>
      )}

      <hr className="border-surface-border" />

      <p className="text-[10px] text-slate-500 uppercase tracking-widest">Company tech profile</p>
      <div className="grid grid-cols-2 gap-3">
        <label className="block text-xs text-slate-400">
          Stage
          <select
            value={draft.company_profile.stage}
            onChange={(e) => patchProfile({ stage: e.target.value })}
            className="mt-1 w-full px-2 py-1.5 rounded border border-surface-border bg-surface text-slate-200"
          >
            {STAGE_OPTIONS.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </label>
        <label className="block text-xs text-slate-400">
          Team size
          <select
            value={draft.company_profile.team_size_range}
            onChange={(e) => patchProfile({ team_size_range: e.target.value })}
            className="mt-1 w-full px-2 py-1.5 rounded border border-surface-border bg-surface text-slate-200"
          >
            {TEAM_OPTIONS.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </label>
      </div>
      <label className="block text-xs text-slate-400">
        Industry (leave blank for stealth)
        <input
          type="text"
          value={draft.company_profile.industry_broad ?? ""}
          onChange={(e) =>
            patchProfile({ industry_broad: e.target.value.trim() || null })
          }
          placeholder="e.g. Fintech Infrastructure"
          className="mt-1 w-full px-2 py-1.5 rounded border border-surface-border bg-surface text-slate-200"
        />
      </label>
      <label className="block text-xs text-slate-400">
        Tech stack (comma-separated)
        <input
          type="text"
          value={draft.company_profile.tech_stack.join(", ")}
          onChange={(e) => patchStack(e.target.value)}
          className="mt-1 w-full px-2 py-1.5 rounded border border-surface-border bg-surface text-slate-200"
        />
      </label>
    </div>
  );
}
