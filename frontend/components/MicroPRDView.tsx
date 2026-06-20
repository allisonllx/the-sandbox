import type { MicroPRD } from "@/lib/types";

const SECTIONS = [
  { key: "context", label: "Context", render: (p: MicroPRD) => p.context, list: false },
  { key: "success", label: "Definition of Success", render: (p: MicroPRD) => p.definition_of_success, list: true },
  { key: "constraints", label: "Structural Constraints", render: (p: MicroPRD) => p.structural_constraints, list: true },
  { key: "instructions", label: "Sandbox Instructions", render: (p: MicroPRD) => p.sandbox_instructions, list: true },
] as const;

export function MicroPRDView({ prd }: { prd: MicroPRD }) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-slate-100">{prd.title}</h2>
      </div>
      {SECTIONS.map(({ key, label, render, list }) => {
        const content = render(prd);
        return (
          <section key={key} className="space-y-2">
            <h3 className="text-[11px] uppercase tracking-widest text-slate-500 font-semibold">
              {label}
            </h3>
            {list ? (
              <ul className="space-y-2">
                {(content as string[]).map((item, i) => (
                  <li key={i} className="text-sm text-slate-300 flex gap-2">
                    <span className="text-accent flex-shrink-0">›</span>
                    {item}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-slate-300 leading-relaxed">{content as string}</p>
            )}
          </section>
        );
      })}
    </div>
  );
}
