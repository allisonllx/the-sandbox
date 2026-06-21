# Design Rationale — EatsHub

## Target persona

Office worker on a 30-minute lunch break, mobile-first, wants nearby food with accurate wait times and a frictionless cart.

## Problem framing

Merchant discovery is scattered across tabs and filters. Success means: scan nearby options → pick one → add to cart → checkout in three taps or fewer.

## Information architecture

- **List-first on mobile** (thumb-friendly); two-column layout from 768px up with cart drawer pinned right.
- Flow: merchant list → tap card → item lands in cart → checkout button enables.
- Trade-off: skipped map view in v1 to ship faster; map would be phase-two for spatial discovery.

## Stack & implementation choices

- Vanilla HTML/CSS/JS — no build step for hackathon velocity.
- `@media (min-width: 768px)` grid for responsive layout; dark theme for contrast in demo.
- Cart state held in a simple in-memory array; would move to session storage for persistence.

## Open questions / future work

- Default list vs map on first open (A/B).
- Wait-time estimates: static mock vs live API.
- Accessibility audit for screen-reader labels on cart drawer.
