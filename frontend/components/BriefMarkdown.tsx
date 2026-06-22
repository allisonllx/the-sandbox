import type { ReactNode } from "react";

/** Inline **bold** and `code` — briefs use a small markdown subset only. */
export function BriefMarkdownInline({
  content,
  className = "text-sm text-slate-300 leading-relaxed",
}: {
  content: string;
  className?: string;
}) {
  return <span className={className}>{renderInline(content, "inline")}</span>;
}

function renderInline(text: string, keyPrefix: string): ReactNode[] {
  const parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`)/g);
  return parts.map((part, index) => {
    const key = `${keyPrefix}-${index}`;
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        <strong key={key} className="font-semibold text-slate-200">
          {part.slice(2, -2)}
        </strong>
      );
    }
    if (part.startsWith("`") && part.endsWith("`")) {
      return (
        <code key={key} className="text-accent/90">
          {part.slice(1, -1)}
        </code>
      );
    }
    return part;
  });
}

function listIndent(line: string): number {
  const match = line.match(/^(\s*)-/);
  if (!match) return -1;
  return Math.floor(match[1].length / 2);
}

interface ListTreeNode {
  text: string;
  children: ListTreeNode[];
}

function collectListLines(lines: string[], start: number): { flat: { depth: number; text: string }[]; next: number } {
  const flat: { depth: number; text: string }[] = [];
  let index = start;
  while (index < lines.length) {
    const line = lines[index];
    if (line.trim() === "") break;
    const depth = listIndent(line);
    if (depth < 0) break;
    flat.push({ depth, text: line.replace(/^\s*-\s+/, "") });
    index += 1;
  }
  return { flat, next: index };
}

function buildListTree(flat: { depth: number; text: string }[]): ListTreeNode[] {
  const root: ListTreeNode[] = [];
  const stack: { depth: number; children: ListTreeNode[] }[] = [{ depth: -1, children: root }];

  for (const { depth, text } of flat) {
    while (stack[stack.length - 1].depth >= depth) {
      stack.pop();
    }
    const node: ListTreeNode = { text, children: [] };
    stack[stack.length - 1].children.push(node);
    stack.push({ depth, children: node.children });
  }

  return root;
}

function renderListTreeRecursive(nodes: ListTreeNode[], keyPrefix: string): ReactNode {
  return (
    <ul className="space-y-2 list-none">
      {nodes.map((node, index) => {
        const key = `${keyPrefix}-${index}`;
        return (
          <li key={key} className="text-sm text-slate-300 leading-relaxed">
            {renderInline(node.text, key)}
            {node.children.length > 0 && (
              <div className="mt-1.5 ml-4 border-l border-surface-border pl-3">
                {renderListTreeRecursive(node.children, `${key}-nested`)}
              </div>
            )}
          </li>
        );
      })}
    </ul>
  );
}

/**
 * Renders challenge-brief markdown while inheriting the app monospace stack.
 */
export function BriefMarkdown({ content }: { content: string }) {
  const lines = content.split("\n");
  const blocks: ReactNode[] = [];
  let index = 0;
  let blockKey = 0;

  while (index < lines.length) {
    const line = lines[index];
    if (line.trim() === "") {
      index += 1;
      continue;
    }

    if (listIndent(line) >= 0) {
      const { flat, next } = collectListLines(lines, index);
      blocks.push(
        <div key={blockKey}>{renderListTreeRecursive(buildListTree(flat), `list-${blockKey}`)}</div>
      );
      index = next;
      blockKey += 1;
      continue;
    }

    blocks.push(
      <p key={blockKey} className="text-sm text-slate-300 leading-relaxed">
        {renderInline(line, `p-${blockKey}`)}
      </p>
    );
    index += 1;
    blockKey += 1;
  }

  return <div className="space-y-3 font-inherit">{blocks}</div>;
}
