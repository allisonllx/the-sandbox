import type { CompanyTechProfile, MicroPRD } from "@/lib/types";
import { BriefSectionBody } from "./BriefSectionBody";
import { CompanyProfilePanel } from "./CompanyProfilePanel";

const BASE_SECTIONS = [
  { key: "context", label: "Context", render: (p: MicroPRD) => p.context, list: false },
  {
    key: "success",
    label: "Definition of Success",
    render: (p: MicroPRD) => p.definition_of_success,
    list: true,
  },
  {
    key: "constraints",
    label: "Structural Constraints",
    render: (p: MicroPRD) => p.structural_constraints,
    list: true,
  },
  {
    key: "instructions",
    label: "Sandbox Instructions",
    render: (p: MicroPRD) => p.sandbox_instructions,
    list: true,
  },
] as const;

const PRODUCT_SECTIONS = [
  { key: "persona", label: "User Persona", render: (p: MicroPRD) => p.user_persona, list: false },
  {
    key: "framing",
    label: "Problem Framing",
    render: (p: MicroPRD) => p.problem_framing,
    list: false,
  },
  {
    key: "design",
    label: "Design Considerations",
    render: (p: MicroPRD) => p.design_considerations ?? [],
    list: true,
  },
  {
    key: "stack",
    label: "Stack Guidance",
    render: (p: MicroPRD) => p.stack_guidance ?? [],
    list: true,
  },
  {
    key: "deliverables",
    label: "Deliverable Requirements",
    render: (p: MicroPRD) => p.deliverable_requirements ?? [],
    list: true,
  },
] as const;

export function MicroPRDView({
  prd,
  companyProfile,
}: {
  prd: MicroPRD;
  companyProfile?: CompanyTechProfile | null;
}) {
  const isProduct = prd.track === "product_feature";
  const sections = isProduct
    ? [
        BASE_SECTIONS[0],
        ...PRODUCT_SECTIONS,
        BASE_SECTIONS[1],
        BASE_SECTIONS[2],
        BASE_SECTIONS[3],
      ]
    : BASE_SECTIONS;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-slate-100">{prd.title}</h2>
        {companyProfile && (
          <div className="mt-3 p-3 rounded-lg border border-surface-border bg-surface-muted/50">
            <p className="text-[10px] text-slate-500 uppercase tracking-widest mb-2">
              Company Profile (blind audition)
            </p>
            <CompanyProfilePanel profile={companyProfile} compact />
          </div>
        )}
      </div>
      {sections.map(({ key, label, render, list }) => {
        const content = render(prd);
        if (!content || (Array.isArray(content) && content.length === 0)) {
          return null;
        }
        return (
          <section key={key} className="space-y-2">
            <h3 className="text-[11px] uppercase tracking-widest text-slate-500 font-semibold">
              {label}
            </h3>
            <BriefSectionBody content={content} list={list} />
          </section>
        );
      })}
    </div>
  );
}
