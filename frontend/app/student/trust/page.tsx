import Link from "next/link";

export default function StudentTrustPage() {
  return (
    <div className="min-h-screen bg-surface">
      <header className="border-b border-surface-border bg-surface-raised px-6 py-3">
        <div className="max-w-3xl mx-auto flex items-center gap-3">
          <Link href="/student" className="text-xs text-slate-500 hover:text-slate-300">
            ← Innovation Hub
          </Link>
          <span className="text-surface-border">|</span>
          <span className="text-accent font-semibold text-sm tracking-wider">SPONSOR TRUST</span>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-6 py-8 space-y-6 text-sm text-slate-400 leading-relaxed">
        <div>
          <h1 className="text-xl font-semibold text-slate-100">Blind Audition & Sponsor Verification</h1>
          <p className="mt-2">
            Every challenge on this platform uses a double-blind model. You never see the
            sponsoring company&apos;s name — only a standardized Company Tech Profile (stage,
            team size range, stack). This prevents roadmap leaks and prestige bias.
          </p>
        </div>

        <section className="space-y-2">
          <h2 className="text-slate-200 font-medium">Verified Sponsor badge</h2>
          <p>
            Before a challenge goes live, sponsors complete platform onboarding (demo: manual
            review). Challenges with a locked bounty show &quot;Platform-verified sponsor&quot; and
            &quot;Funds verified &amp; locked by platform&quot; — a stub for production escrow.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-slate-200 font-medium">Company Tech Profile</h2>
          <p>
            Profiles use LinkedIn-style team size ranges (e.g. 11–50) and broad industry
            categories. High-sensitivity stealth challenges omit industry entirely so students
            cannot reverse-engineer the sponsor from sector hints alone.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-slate-200 font-medium">Roadmap (not built in demo)</h2>
          <p>
            Production will add Stripe escrow, KYC for sponsors, and student accounts to persist
            Execution Points across devices. This hackathon ships the narrative and data model only.
          </p>
        </section>
      </main>
    </div>
  );
}
