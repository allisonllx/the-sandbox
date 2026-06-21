# Design Rationale — LockerShare

## Target persona

Urban renter without garage space, 28–40, needs occasional power tools or camping gear for weekend projects — price-sensitive, values pickup proximity.

## Problem architecture

Equipment locker discovery must feel like a neutral community inventory network (blind audition — no industry-specific branding in public copy).

## Information architecture

- List view of nearby lockers with distance, daily rate, and availability badge.
- Flow: browse inventory → tap locker → add rental to cart → checkout stub.
- Chose list over map for MVP — fewer geolocation edge cases in prototype.

## Stack & implementation choices

- Static prototype with `mock/inventory.json` — matches published challenge starter paths after domain obfuscation.
- Responsive CSS grid; `@media (min-width: 768px)` splits list and cart.
- Trade-off: checkout is a stub alert — real flow would integrate reservation holds.

## Open questions / future work

- Availability sync with locker hardware API.
- Damage deposit and identity verification steps post-checkout.
