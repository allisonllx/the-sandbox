# Product

## What It Does

The Sandbox is a talent platform that turns a startup's messy internal backlog into structured, safe-to-share coding challenges that student developers can solve to prove their skills. A local privacy filter automatically strips sensitive data before anything leaves the company, so founders can outsource real engineering problems without risking IP leaks. Students get graded by an AI that evaluates not just whether their code works, but whether it reflects professional engineering judgement — bypassing the résumé filters and social networks that usually gate entry-level roles.

## Target Users

**Startup CTOs / Founders / VP Engineering**
Flooded with bug reports, telemetry anomalies, and feature requests they lack the bandwidth to scope for junior developers. They need to offload non-core problems without exposing trade secrets, customer PII, or internal architecture.

**Ambitious Student Developers (University / Early-Career)**
Technically capable but locked out of top roles by the absence of a pedigreed network or enterprise experience. They need a way to demonstrate real-world scaling, debugging, and optimization taste on production-grade problems — not toy tutorials.

## Core User Flows

1. **Startup: Ingest & sanitize** — Paste or upload raw logs/feedback into the local client. The privacy proxy scrubs PII and extracts structural metadata without sending any content externally.

2. **Startup: Triage & de-risk** — The AI PM ranks the backlog by Severity, Friction, and Sensitivity. The founder reviews the Red/Yellow/Green tags, applies Relaxation Controls (abstract logic, synthesize variable names, inject statistical noise), and approves a challenge for publication.

3. **Student: Discover & set up** — Browse published challenges, read the Micro-PRD, and download a custom-generated synthetic dataset that mirrors the structural complexity of the real problem.

4. **Student: Solve & submit** — Write and run code in the interactive browser terminal, then submit a solution.

5. **Startup: Review matches** — The AI Assessor scores each submission automatically. Top-performing candidates are surfaced in the CTO's matching dashboard with a full taste-and-judgment scorecard.

## Out of Scope

- The platform does not transmit raw startup data (logs, database rows, customer records) to any external service — ever.
- The platform does not conduct interviews, make hiring decisions, or manage employment contracts.
- Students do not interact with any real corporate infrastructure; they work entirely against synthetic datasets.
- The platform does not replace or compete with existing ATS (Applicant Tracking Systems) — it feeds verified candidate signals into the top of the hiring funnel only.

## Roadmap / Known Gaps

- **Hackathon MVP scope:** End-to-end demo loop — ingest 5 lines of log text → privacy proxy → relaxation toggle → published challenge → mock submission → AI Assessor scorecard.
- **Not yet built:** User authentication, billing, persistent user profiles, multi-tenant startup isolation, production-grade code runner scaling.
- **Open decision:** Cloud deployment target (AWS, GCP, Fly.io) and whether the privacy proxy ships as a standalone CLI binary or an Electron app.
- **Open decision:** LLM provider selection (OpenAI vs Anthropic) and whether taste evaluation uses a fine-tuned model or a prompt-engineered general model.
