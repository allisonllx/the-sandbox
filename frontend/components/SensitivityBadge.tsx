import type { SensitivityTag } from "@/lib/types";

const STYLES: Record<SensitivityTag, string> = {
  red: "bg-red-500/15 text-red-400 border border-red-500/30",
  yellow: "bg-yellow-500/15 text-yellow-400 border border-yellow-500/30",
  green: "bg-green-500/15 text-green-400 border border-green-500/30",
};

const LABELS: Record<SensitivityTag, string> = {
  red: "● HIGH RISK",
  yellow: "● MED RISK",
  green: "● LOW RISK",
};

export function SensitivityBadge({ tag }: { tag: SensitivityTag }) {
  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold tracking-widest uppercase ${STYLES[tag]}`}
    >
      {LABELS[tag]}
    </span>
  );
}
