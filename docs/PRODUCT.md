# Product

## What It Does

The Sandbox is an **Innovation Hub** — a talent platform that turns a startup's messy internal backlog into structured, safe-to-share challenges across multiple innovation tracks.

**Technical** challenges are **greenfield system-module sprints** (webhook handlers, idempotency stores, stream parsers, etc.) — not LeetCode drills and not legacy OSS contributions. Students get an interface spec (`docs/SPEC.md`), public tests, and minimal stubs; typical onboarding is under 30 minutes.

**Product Feature** challenges focus on UX reasoning, prototype delivery, and design trade-offs documented in `DESIGN.md`.

A local privacy filter automatically strips sensitive data before anything leaves the company, so founders can outsource real problems without risking IP leaks.

## Target Users

**Startup CTOs / Founders / VP Engineering**
Flooded with bug reports, telemetry anomalies, and feature requests they lack the bandwidth to scope for junior developers. They need to offload non-core problems without exposing trade secrets, customer PII, or internal architecture.

**Ambitious Student Developers (University / Early-Career)**
Technically capable but locked out of top roles by the absence of a pedigreed network or enterprise experience. They need a way to demonstrate real-world scaling, debugging, and optimization taste on production-grade problems — not toy tutorials.

## Core User Flows

1. **Startup: Ingest & sanitize** — Three paths: **Upload UI** at `/startup/upload` (task description or log file → loading page runs sanitize then score), **quick intake** on `/startup` (`POST /triage/intake`), or API/scripts. The privacy proxy scrubs PII locally and extracts structural metadata; sensitivity scoring runs on metadata only.

2. **Startup: Triage & de-risk** — The AI PM ranks the backlog by Severity, Friction, and Sensitivity, suggests an **innovation track** (Technical or Product Feature for MVP), and applies Relaxation Controls. **Preview Changes** runs the **Challenge Factory** for non-demo technical items: a single-pass **TechnicalChallengeSpec** (archetype + interface contract) drives starter generation and validation; Micro-PRD is projected from the spec. Founders see internal `brand_proxy`; students receive a **Company Tech Profile** only (blind audition). Preview returns `PublishDraft` + `challenge_package` (+ optional `challenge_spec`) — founders edit title, context, blueprint override, success criteria, and company profile before **Approve & Publish**.

   **Product track** items (e.g. `demo-004`, merchant-discovery briefs) skip the dynamic factory at Preview — they receive the hardcoded frontend starter at publish.

3. **Student: Discover & set up** — Browse the Innovation Hub with track filter tabs. Each challenge shows stage, team size range, and tech stack — never the sponsor name. Technical challenges include a synthetic SQLite dataset; Product Feature challenges include a frontend starter scaffold and required `DESIGN.md` template.

4. **Student: Solve & submit** — Technical track: Monaco workspace + public tests + multi-file submit. Product track: prototype editor + optional Figma/deploy links + `DESIGN.md` in submit manifest.

5. **Startup: Review matches** — Track-aware assessor plugins score submissions (Technical: tests + taste; Product: structure + DESIGN.md rubric). Scorecard dimensions differ by track. After publish, sponsors open **Sponsor Match Radar** at `/startup/matches/{challengeId}` — ranked performers for **that challenge only** (live submissions or demo stubs). They do not see other companies' challenges or the student global leaderboard.

6. **Rank surfaces (demo stubs)** — **Students** use `/student/leaderboard` for global Execution Points (platform signal only). **Startups** use `/startup/matches/{id}` ranked by **Sponsor Fit** for that challenge. **Enterprises** use `/enterprise/radar` for platform-wide top tier. A student can rank highly globally while not topping a specific sponsor's Match Radar — and vice versa.

> **Execution Points measure platform-verified engineering signal, not sponsor preference.** Sponsors grade fit to *their* success criteria; the platform grades proof-of-work against track-standard benchmarks.

## Defensive Posture (Hackathon Narrative)

The platform addresses three existential B2B talent risks with **hybrid demo mechanics** — some rules are real, others are credible UI stubs:

| Risk | Mitigation | Demo depth |
|---|---|---|
| **Free labor / exploitation** | Guaranteed reward locked before publish; AI PM scope cap (~8h) | Real scope gate + stubbed bounty/interview lock |
| **Stealth roadmap leak** | **Blind Audition**: Company Tech Profile replaces sponsor identity; domain obfuscation + column renames for high-sensitivity items | Real public API boundary + domain transform |
| **FAANG prestige bias** | **Execution Points** from platform signal only; sponsor fit is per-challenge | Dual-layer scorecard: global EP ≠ sponsor Match Radar rank |
| **Scam bounties** | Platform-verified sponsor badge + escrow label (stub) | Per-challenge verification metadata; `/student/trust` narrative |

> *"We aren't a job board; we are a zero-trust proof-of-work protocol."*

Demo backlog profiles (CTO-only labels): **StealthCo** (`demo-005`), **NovaPay** (`demo-003` bounty), **Platform Pool** (`demo-006`), scope rejection (`demo-007`). Students never see these names.

## Out of Scope

- The platform does not transmit raw startup data (logs, database rows, customer records) to any external service — ever.
- The platform does not conduct interviews, make hiring decisions, or manage employment contracts.
- Students do not interact with any real corporate infrastructure; they work entirely against synthetic datasets.
- The platform does not replace or compete with existing ATS (Applicant Tracking Systems) — it feeds verified candidate signals into the top of the hiring funnel only.

## Roadmap / Known Gaps

- **Hackathon MVP scope:** Two active tracks — **Technical** + **Product Feature**; Automation / AI Governance / Strategy registered as taxonomy with "Coming soon" UI.
- **Shipped (hackathon):** Founder upload UI (`/startup/upload`), `POST /triage/intake`, dynamic challenge factory (TechnicalChallengeSpec + 8 system-module archetypes at Preview).
- **Not yet built:** User authentication, billing, persistent user profiles, multi-tenant startup isolation, production-grade code runner scaling, real Stripe escrow, sponsor KYC.
- **Shipped (hackathon):** Blind audition Company Tech Profile on all public challenges; auth + multi-tenant deferred to post-MVP.
- **Open decision:** Cloud deployment target (AWS, GCP, Fly.io) and whether the privacy proxy ships as a standalone CLI binary or an Electron app.
- **Open decision:** LLM provider selection (OpenAI vs Anthropic) and whether taste evaluation uses a fine-tuned model or a prompt-engineered general model.
