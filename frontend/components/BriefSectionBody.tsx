import type { ReactNode } from "react";
import { BriefMarkdown, BriefMarkdownInline } from "./BriefMarkdown";

/** Renders string or string[] brief content with markdown support. */
export function BriefSectionBody({
  content,
  list = false,
  listMarker = "›",
  listMarkerClassName = "text-accent flex-shrink-0",
  itemClassName = "text-sm text-slate-300 flex gap-2 leading-relaxed",
  inlineClassName,
}: {
  content: string | string[];
  list?: boolean;
  listMarker?: string;
  listMarkerClassName?: string;
  itemClassName?: string;
  inlineClassName?: string;
}) {
  if (list) {
    const items = content as string[];
    return (
      <ul className="space-y-2">
        {items.map((item, index) => (
          <li key={index} className={itemClassName}>
            <span className={listMarkerClassName}>{listMarker}</span>
            <span className="min-w-0 flex-1">
              {item.includes("\n") || item.trimStart().startsWith("- ") ? (
                <BriefMarkdown content={item} />
              ) : (
                <BriefMarkdownInline content={item} className={inlineClassName} />
              )}
            </span>
          </li>
        ))}
      </ul>
    );
  }

  return <BriefMarkdown content={content as string} />;
}

/** Left-panel subsection with uppercase label. */
export function BriefAsideSection({
  label,
  children,
  className = "mt-8 pt-6 border-t border-surface-border space-y-2",
}: {
  label: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={className}>
      <h3 className="text-[11px] uppercase tracking-widest text-slate-500 font-semibold">{label}</h3>
      {children}
    </div>
  );
}
