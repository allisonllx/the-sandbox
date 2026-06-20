interface ScoreBarProps {
  label: string;
  value: number;
  color: string;
}

export function ScoreBar({ label, value, color }: ScoreBarProps) {
  return (
    <div className="space-y-1">
      <div className="flex justify-between items-center">
        <span className="text-[11px] text-slate-400 uppercase tracking-wider">{label}</span>
        <span className="text-[11px] font-semibold text-slate-200">{value}</span>
      </div>
      <div className="h-1.5 bg-surface-muted rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${color}`}
          style={{ width: `${value}%` }}
        />
      </div>
    </div>
  );
}
