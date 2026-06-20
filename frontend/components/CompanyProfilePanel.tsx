import type { CompanyTechProfile } from "@/lib/types";

export function CompanyProfilePanel({
  profile,
  compact = false,
}: {
  profile: CompanyTechProfile;
  compact?: boolean;
}) {
  const parts = [
    profile.stage,
    profile.team_size_range ? `Team ${profile.team_size_range}` : null,
    profile.industry_broad,
  ].filter(Boolean);

  return (
    <div className={compact ? "space-y-1" : "space-y-2"}>
      <p
        className={`text-slate-400 ${compact ? "text-[10px]" : "text-xs"} leading-relaxed`}
      >
        {parts.join(" · ")}
      </p>
      <div className="flex flex-wrap gap-1">
        {profile.tech_stack.map((tech) => (
          <span
            key={tech}
            className="text-[10px] px-1.5 py-0.5 rounded bg-surface-muted text-slate-500 border border-surface-border"
          >
            {tech}
          </span>
        ))}
      </div>
      {profile.verification_status === "verified" && (
        <span className="inline-block text-[10px] uppercase tracking-widest px-2 py-0.5 rounded border border-green-500/40 text-green-400 bg-green-500/10">
          {profile.verification_label}
        </span>
      )}
    </div>
  );
}

export function RewardBadges({
  reward,
  escrowLabel,
}: {
  reward?: { reward_type: string; amount_usd?: number | null; interview_benchmark?: number; locked: boolean } | null;
  escrowLabel?: string | null;
}) {
  if (!reward?.locked) return null;
  return (
    <div className="flex flex-wrap gap-2">
      <span className="text-[10px] uppercase tracking-widest px-2 py-0.5 rounded border border-amber-500/40 text-amber-400 bg-amber-500/10">
        {reward.reward_type === "cash_bounty"
          ? `$${reward.amount_usd ?? 500} Bounty Locked`
          : `Interview Pass ≥${reward.interview_benchmark ?? 75}`}
      </span>
      {escrowLabel && (
        <span className="text-[10px] uppercase tracking-widest px-2 py-0.5 rounded border border-slate-600 text-slate-500">
          {escrowLabel}
        </span>
      )}
    </div>
  );
}
