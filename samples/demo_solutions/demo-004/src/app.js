// EatsHub discovery — extend this starter
let merchants = [];
let cart = [];

async function loadMerchants() {
  const res = await fetch('mock/merchants.json');
  const data = await res.json();
  merchants = data.merchants || [];
  renderMerchants();
}

function renderMerchants() {
  const root = document.getElementById('merchant-list');
  root.innerHTML = '<h2>Nearby merchants</h2>';
  merchants.forEach((m) => {
    const el = document.createElement('div');
    el.className = 'merchant-card';
    const meta = m.wait_min != null
      ? `${m.distance_km} km · ~${m.wait_min} min wait · ★ ${m.rating}`
      : `${m.distance_km} km · $${m.daily_rate}/day · ${m.available ? 'Available' : 'Reserved'}`;
    el.innerHTML = `<strong>${m.name}</strong><br/>${meta}`;
    el.onclick = () => addToCart(m);
    root.appendChild(el);
  });
}

function addToCart(merchant) {
  cart.push({ ...merchant, price: 12.5 });
  renderCart();
}

function renderCart() {
  const list = document.getElementById('cart-items');
  const total = document.getElementById('cart-total');
  const btn = document.getElementById('checkout-btn');
  list.innerHTML = cart.map((c) => `<li>${c.name} — $${c.price.toFixed(2)}</li>`).join('');
  const sum = cart.reduce((a, c) => a + c.price, 0);
  total.textContent = `Total: $${sum.toFixed(2)}`;
  btn.disabled = cart.length === 0;
}

document.getElementById('checkout-btn').addEventListener('click', () => {
  alert('Checkout stub — implement frictionless flow in your solution');
});

loadMerchants().catch(console.error);
