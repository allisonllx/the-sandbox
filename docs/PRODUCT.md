# Product

## What It Does

The Sandbox is an **Innovation Hub** — a talent platform that turns a startup's messy internal backlog into structured, safe-to-share challenges across multiple innovation tracks. **Technical** challenges focus on debugging and optimization; **Product Feature** challenges focus on UX reasoning, prototype delivery, and design trade-offs documented in `DESIGN.md`. A local privacy filter automatically strips sensitive data before anything leaves the company, so founders can outsource real problems without risking IP leaks.

## Target Users

**Startup CTOs / Founders / VP Engineering**
Flooded with bug reports, telemetry anomalies, and feature requests they lack the bandwidth to scope for junior developers. They need to offload non-core problems without exposing trade secrets, customer PII, or internal architecture.

**Ambitious Student Developers (University / Early-Career)**
Technically capable but locked out of top roles by the absence of a pedigreed network or enterprise experience. They need a way to demonstrate real-world scaling, debugging, and optimization taste on production-grade problems — not toy tutorials.

## Core User Flows

1. **Startup: Ingest & sanitize** — Paste or upload raw logs/feedback into the local client. The privacy proxy scrubs PII and extracts structural metadata without sending any content externally.

2. **Startup: Triage & de-risk** — The AI PM ranks the backlog by Severity, Friction, and Sensitivity, suggests an **innovation track** (Technical or Product Feature for MVP), and applies Relaxation Controls. Founders see internal `brand_proxy`; students receive a **Company Tech Profile** only (blind audition).

3. **Student: Discover & set up** — Browse the Innovation Hub with track filter tabs. Each challenge shows stage, team size range, and tech stack — never the sponsor name. Technical challenges include a synthetic SQLite dataset; Product Feature challenges include a frontend starter scaffold and required `DESIGN.md` template.

4. **Student: Solve & submit** — Technical track: Monaco workspace + public tests + multi-file submit. Product track: prototype editor + optional Figma/deploy links + `DESIGN.md` in submit manifest.

5. **Startup: Review matches** — Track-aware assessor plugins score submissions (Technical: tests + taste; Product: structure + DESIGN.md rubric). Scorecard dimensions differ by track.

## Defensive Posture (Hackathon Narrative)

The platform addresses three existential B2B talent risks with **hybrid demo mechanics** — some rules are real, others are credible UI stubs:

| Risk | Mitigation | Demo depth |
|---|---|---|
| **Free labor / exploitation** | Guaranteed reward locked before publish; AI PM scope cap (~8h) | Real scope gate + stubbed bounty/interview lock |
| **Stealth roadmap leak** | **Blind Audition**: Company Tech Profile replaces sponsor identity; domain obfuscation + column renames for high-sensitivity items | Real public API boundary + domain transform |
| **FAANG prestige bias** | **Execution Points** rank decoupled from company logos; enterprise reverse-sourcing radar | Stub leaderboard + `/enterprise/radar` |
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
- **Not yet built:** User authentication, billing, persistent user profiles, multi-tenant startup isolation, production-grade code runner scaling, real Stripe escrow, sponsor KYC.
- **Shipped (hackathon):** Blind audition Company Tech Profile on all public challenges; auth + multi-tenant deferred to post-MVP.
- **Open decision:** Cloud deployment target (AWS, GCP, Fly.io) and whether the privacy proxy ships as a standalone CLI binary or an Electron app.
- **Open decision:** LLM provider selection (OpenAI vs Anthropic) and whether taste evaluation uses a fine-tuned model or a prompt-engineered general model.
