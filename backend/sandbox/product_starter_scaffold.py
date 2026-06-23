"""Frontend starter scaffold for Product Feature track challenges."""

from __future__ import annotations

from .starter_scaffold import browser_workspace_readme_section

PRODUCT_STARTER_PATHS = (
    "README.md",
    "DESIGN.md",
    "mock/merchants.json",
    "index.html",
    "src/styles.css",
    "src/app.js",
)


def generate_product_starter_files(
    challenge_id: str,
    title: str,
    brand_proxy: str,
    domain_proxy: str | None = None,
) -> dict[str, str]:
    equipment = domain_proxy == "hyperlocal_equipment"
    mock_path = "mock/inventory.json" if equipment else "mock/merchants.json"
    return {
        "README.md": _readme(challenge_id, title, brand_proxy, equipment=equipment),
        "DESIGN.md": _design_md(brand_proxy, equipment=equipment),
        mock_path: _inventory_json(brand_proxy) if equipment else _merchants_json(brand_proxy),
        "index.html": _index_html(brand_proxy, equipment=equipment),
        "src/styles.css": _styles_css(),
        "src/app.js": _app_js(brand_proxy, equipment=equipment),
    }


def product_platform_instructions(*, equipment_mode: bool = False) -> list[str]:
    noun = "inventory locker" if equipment_mode else "merchant"
    mock_file = "mock/inventory.json" if equipment_mode else "mock/merchants.json"
    return [
        "Read the Product Feature brief in the left panel — note persona, design considerations, and deliverables.",
        "The starter prototype loads in the editor (index.html, src/app.js, src/styles.css).",
        "Complete **DESIGN.md** with your personas, layout trade-offs, and stack choices — this is required.",
        f"Use {mock_file} for local {noun} data; extend the UI for discovery + cart checkout.",
        "Optional: add Figma or deployed preview links in the submit panel.",
        "**No terminal** and **no in-browser live site preview** — edit files in the workspace; open HTML locally if you download the Starter ZIP.",
        "Click **Submit Project** when ready (includes DESIGN.md + code).",
    ]


def _readme(challenge_id: str, title: str, brand: str, *, equipment: bool = False) -> str:
    deliverable = "equipment locker discovery + cart" if equipment else "merchant discovery + cart"
    return f"""# {title}

Challenge: `{challenge_id}` · Brand: **{brand}**

## Deliverables

1. **DESIGN.md** — personas, IA trade-offs, stack rationale (required)
2. **Prototype** — responsive {deliverable} (edit starter files)
3. Optional external links — Figma or deployed preview URL at submit time

## Local preview

Open `index.html` in a browser or use any static server (download Starter ZIP — not available inside the platform editor).
{browser_workspace_readme_section(technical=False)}"""


def _design_md(brand: str, *, equipment: bool = False) -> str:
    entity = "locker / inventory item" if equipment else "merchant"
    return f"""# Design Rationale — {brand}

## Target persona

Who is the primary user? What job are they trying to get done?

## Problem framing

What problem does this feature solve? What does success look like?

## Information architecture

- Map vs list view — which did you choose and why?
- How does the user move from discovery → {entity} detail → checkout?

## Stack & implementation choices

- Why this approach for layout/state?
- Trade-offs considered (speed vs polish, mobile vs desktop, etc.)

## Open questions / future work

What would you validate next with real users?
"""


def _inventory_json(brand: str) -> str:
    return f"""{{
  "brand": "{brand}",
  "inventory": [
    {{ "id": "l1", "name": "Cordless Drill Kit", "distance_km": 0.3, "available": true, "daily_rate": 18.0, "tags": ["tools", "diy"] }},
    {{ "id": "l2", "name": "Pressure Washer", "distance_km": 0.6, "available": true, "daily_rate": 24.0, "tags": ["outdoor", "cleaning"] }},
    {{ "id": "l3", "name": "Camping Tent (4p)", "distance_km": 1.1, "available": false, "daily_rate": 15.0, "tags": ["outdoor", "gear"] }},
    {{ "id": "l4", "name": "Mountain Bike", "distance_km": 1.4, "available": true, "daily_rate": 22.0, "tags": ["sport", "bike"] }}
  ]
}}
"""


def _merchants_json(brand: str) -> str:
    return f"""{{
  "brand": "{brand}",
  "merchants": [
    {{ "id": "m1", "name": "River Noodle House", "distance_km": 0.4, "wait_min": 5, "rating": 4.6, "tags": ["noodles", "quick"] }},
    {{ "id": "m2", "name": "Green Bowl Co", "distance_km": 0.8, "wait_min": 12, "rating": 4.4, "tags": ["healthy", "bowls"] }},
    {{ "id": "m3", "name": "Late Night Slice", "distance_km": 1.2, "wait_min": 20, "rating": 4.2, "tags": ["pizza", "late"] }},
    {{ "id": "m4", "name": "Harbor Sushi", "distance_km": 1.5, "wait_min": 25, "rating": 4.8, "tags": ["sushi", "premium"] }}
  ]
}}
"""


def _index_html(brand: str, *, equipment: bool = False) -> str:
    label = "Equipment Discovery" if equipment else "Merchant Discovery"
    list_label = "Inventory nearby" if equipment else "Merchants nearby"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{brand} — {label}</title>
  <link rel="stylesheet" href="src/styles.css" />
</head>
<body>
  <header class="app-header">
    <h1>{brand}</h1>
    <p class="subtitle">Local {label.lower()} — starter prototype</p>
  </header>
  <main class="layout">
    <section id="merchant-list" class="panel" aria-label="{list_label}"></section>
    <aside id="cart-drawer" class="panel cart" aria-label="Cart">
      <h2>Cart</h2>
      <ul id="cart-items"></ul>
      <p id="cart-total">Total: $0.00</p>
      <button id="checkout-btn" type="button" disabled>Checkout</button>
    </aside>
  </main>
  <script src="src/app.js"></script>
</body>
</html>
"""


def _styles_css() -> str:
    return """/* Starter styles — extend for responsive 375px–1280px */
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: system-ui, sans-serif;
  background: #0f1115;
  color: #e2e8f0;
}
.app-header { padding: 1rem 1.25rem; border-bottom: 1px solid #2a2f3a; }
.subtitle { color: #94a3b8; font-size: 0.875rem; margin: 0.25rem 0 0; }
.layout {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1rem;
  padding: 1rem;
}
@media (min-width: 768px) {
  .layout { grid-template-columns: 2fr 1fr; }
}
.panel {
  background: #1a1d24;
  border: 1px solid #2a2f3a;
  border-radius: 8px;
  padding: 1rem;
}
.merchant-card {
  border: 1px solid #334155;
  border-radius: 6px;
  padding: 0.75rem;
  margin-bottom: 0.5rem;
  cursor: pointer;
}
.merchant-card:hover { border-color: #6366f1; }
.cart ul { list-style: none; padding: 0; min-height: 4rem; }
#checkout-btn {
  width: 100%;
  padding: 0.5rem;
  background: #6366f1;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}
#checkout-btn:disabled { opacity: 0.4; cursor: not-allowed; }
"""


def _app_js(brand: str, *, equipment: bool = False) -> str:
    mock_file = "mock/inventory.json" if equipment else "mock/merchants.json"
    data_key = "inventory" if equipment else "merchants"
    heading = "Nearby inventory" if equipment else "Nearby merchants"
    return f"""// {brand} discovery — extend this starter
let merchants = [];
let cart = [];

async function loadMerchants() {{
  const res = await fetch('{mock_file}');
  const data = await res.json();
  merchants = data.{data_key} || [];
  renderMerchants();
}}

function renderMerchants() {{
  const root = document.getElementById('merchant-list');
  root.innerHTML = '<h2>{heading}</h2>';
  merchants.forEach((m) => {{
    const el = document.createElement('div');
    el.className = 'merchant-card';
    const meta = m.wait_min != null
      ? `${{m.distance_km}} km · ~${{m.wait_min}} min wait · ★ ${{m.rating}}`
      : `${{m.distance_km}} km · $${{m.daily_rate}}/day · ${{m.available ? 'Available' : 'Reserved'}}`;
    el.innerHTML = `<strong>${{m.name}}</strong><br/>${{meta}}`;
    el.onclick = () => addToCart(m);
    root.appendChild(el);
  }});
}}

function addToCart(merchant) {{
  cart.push({{ ...merchant, price: 12.5 }});
  renderCart();
}}

function renderCart() {{
  const list = document.getElementById('cart-items');
  const total = document.getElementById('cart-total');
  const btn = document.getElementById('checkout-btn');
  list.innerHTML = cart.map((c) => `<li>${{c.name}} — $${{c.price.toFixed(2)}}</li>`).join('');
  const sum = cart.reduce((a, c) => a + c.price, 0);
  total.textContent = `Total: $${{sum.toFixed(2)}}`;
  btn.disabled = cart.length === 0;
}}

document.getElementById('checkout-btn').addEventListener('click', () => {{
  alert('Checkout stub — implement frictionless flow in your solution');
}});

loadMerchants().catch(console.error);
"""
