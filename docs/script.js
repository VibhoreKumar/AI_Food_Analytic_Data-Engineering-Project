const PALETTE = ['#4f7fe0', '#f2994a', '#e8462f', '#17a398', '#8b6bf2', '#35b06b'];
const MUTED = '#6b7080';
const LINE = '#e7e8ee';

document.getElementById('updated-at').textContent =
  'Updated ' + new Date().toLocaleDateString('en-IN', { year: 'numeric', month: 'short', day: 'numeric' });

Chart.defaults.color = MUTED;
Chart.defaults.font.family = "'Inter', sans-serif";
Chart.defaults.font.size = 11;

async function loadJSON(name) {
  const res = await fetch(`data/${name}.json`);
  if (!res.ok) throw new Error(`Failed to load ${name}.json`);
  return res.json();
}
function fmtNum(n) { return new Intl.NumberFormat('en-IN').format(Math.round(n)); }
function fmtMonth(m) { return new Date(m).toLocaleDateString('en-IN', { month: 'short', year: '2-digit' }); }
function norm(row) { const o = {}; for (const k in row) o[k.toLowerCase()] = row[k]; return o; }

let raw = { revenue: [], restaurants: [], sla: [], summary: [] };
let allCities = [], allMonths = [];
let selectedCities = new Set();
let monthFrom = null, monthTo = null;
let charts = {};

async function init() {
  try {
    const [revenue, restaurants, sla, summary] = await Promise.all([
      loadJSON('city_revenue'), loadJSON('restaurant_performance'),
      loadJSON('delivery_sla'), loadJSON('summary_stats'),
    ]);
    raw.revenue = revenue.map(norm);
    raw.restaurants = restaurants.map(norm);
    raw.sla = sla.map(norm);
    raw.summary = summary.map(norm);

    const totals = {};
    raw.revenue.forEach(r => { totals[r.city] = (totals[r.city] || 0) + Number(r.gmv); });
    allCities = Object.entries(totals).sort((a, b) => b[1] - a[1]).map(d => d[0]);
    selectedCities = new Set(allCities);

    allMonths = [...new Set(raw.revenue.map(r => r.month))].sort();
    monthFrom = allMonths[0];
    monthTo = allMonths[allMonths.length - 1];

    document.getElementById('lede').textContent =
      `${fmtNum(raw.summary[0]?.total_orders || 0)} orders across ${allCities.length} cities, pulled from the warehouse and broken down by restaurant, delivery time and revenue.`;

    buildFilterUI();
    renderKPIs();
    renderAll();
  } catch (err) {
    console.error(err);
    document.getElementById('lede').textContent = 'Could not load dashboard data — check that data/*.json exist.';
  }
}

function buildFilterUI() {
  const chipEl = document.getElementById('city-chips');
  chipEl.innerHTML = allCities.map(c => `<button class="chip active" data-city="${c}">${c}</button>`).join('');
  chipEl.addEventListener('click', e => {
    const btn = e.target.closest('.chip');
    if (!btn) return;
    const city = btn.dataset.city;
    if (selectedCities.has(city)) selectedCities.delete(city); else selectedCities.add(city);
    btn.classList.toggle('active');
    renderAll();
  });

  const fromEl = document.getElementById('month-from');
  const toEl = document.getElementById('month-to');
  fromEl.innerHTML = allMonths.map(m => `<option value="${m}">${fmtMonth(m)}</option>`).join('');
  toEl.innerHTML = allMonths.map(m => `<option value="${m}">${fmtMonth(m)}</option>`).join('');
  fromEl.value = monthFrom;
  toEl.value = monthTo;
  fromEl.addEventListener('change', () => { monthFrom = fromEl.value; renderAll(); });
  toEl.addEventListener('change', () => { monthTo = toEl.value; renderAll(); });

  document.getElementById('reset-filters').addEventListener('click', () => {
    selectedCities = new Set(allCities);
    monthFrom = allMonths[0];
    monthTo = allMonths[allMonths.length - 1];
    chipEl.querySelectorAll('.chip').forEach(c => c.classList.add('active'));
    fromEl.value = monthFrom;
    toEl.value = monthTo;
    renderAll();
  });

  // simple scroll-spy for sidebar nav
  document.querySelectorAll('.nav-item').forEach(a => {
    a.addEventListener('click', () => {
      document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
      a.classList.add('active');
    });
  });
}

function renderKPIs() {
  const row = raw.summary[0] || {};
  const items = [
    ['orders', row.total_orders, PALETTE[0]],
    ['restaurants', row.total_restaurants, PALETTE[1]],
    ['customers', row.total_users, PALETTE[2]],
    ['reviews', row.total_reviews, PALETTE[3]],
  ];
  document.getElementById('kpi-grid').innerHTML = items.map(([label, val, color]) => `
    <div class="kpi" style="border-top-color:${color}">
      <div class="kpi-value">${fmtNum(val || 0)}</div>
      <div class="kpi-label">${label}</div>
    </div>
  `).join('');
}

function getFilteredRevenue() {
  return raw.revenue.filter(r => selectedCities.has(r.city) && r.month >= monthFrom && r.month <= monthTo);
}

function deltaHtml(curr, prev, invert = false) {
  if (prev == null || prev === 0) return `<span class="kpi-delta flat">first month in range</span>`;
  const pct = ((curr - prev) / prev) * 100;
  const good = invert ? pct <= 0 : pct >= 0;
  const cls = Math.abs(pct) < 0.5 ? 'flat' : (good ? 'up' : 'down');
  const arrow = pct >= 0 ? '↑' : '↓';
  return `<span class="kpi-delta ${cls}">${arrow} ${Math.abs(pct).toFixed(1)}% vs prior mo.</span>`;
}

function renderPeriod(filtered) {
  const months = [...new Set(filtered.map(r => r.month))].sort();
  const el = document.getElementById('period-list');
  if (months.length === 0) {
    el.innerHTML = `<p class="empty-note">Widen your filters to see this period.</p>`;
    return;
  }
  const latest = months[months.length - 1];
  const prev = months.length > 1 ? months[months.length - 2] : null;

  function agg(month) {
    const rows = filtered.filter(r => r.month === month);
    const orders = rows.reduce((s, r) => s + Number(r.orders), 0);
    const gmv = rows.reduce((s, r) => s + Number(r.gmv), 0);
    const delivered = rows.reduce((s, r) => s + Number(r.delivered_orders), 0);
    const cancelWeighted = rows.reduce((s, r) => s + Number(r.cancel_rate) * Number(r.orders), 0);
    return { orders, gmv, aov: delivered ? gmv / delivered : 0, cancelRate: orders ? (cancelWeighted / orders) * 100 : 0 };
  }

  const cur = agg(latest);
  const pr = prev ? agg(prev) : null;

  const rows = [
    ['Orders', fmtNum(cur.orders), pr ? deltaHtml(cur.orders, pr.orders) : ''],
    ['GMV', '₹' + fmtNum(cur.gmv), pr ? deltaHtml(cur.gmv, pr.gmv) : ''],
    ['AOV', '₹' + fmtNum(cur.aov), pr ? deltaHtml(cur.aov, pr.aov) : ''],
    ['Cancel rate', cur.cancelRate.toFixed(1) + '%', pr ? deltaHtml(cur.cancelRate, pr.cancelRate, true) : ''],
  ];

  el.innerHTML = rows.map(([label, val, delta]) => `
    <div class="period-row">
      <span class="period-name">${label} · ${fmtMonth(latest)}</span>
      <span style="text-align:right">
        <div class="period-value">${val}</div>
        ${delta}
      </span>
    </div>
  `).join('');
}

function renderRevenue(filtered) {
  const cities = [...selectedCities].filter(c => allCities.includes(c))
    .sort((a, b) => allCities.indexOf(a) - allCities.indexOf(b)).slice(0, 6);
  const months = [...new Set(filtered.map(r => r.month))].sort();
  const labels = months.map(fmtMonth);

  const datasets = cities.map((city, i) => ({
    label: city,
    data: months.map(m => {
      const row = filtered.find(r => r.city === city && r.month === m);
      return row ? Number(row.gmv) : 0;
    }),
    borderColor: PALETTE[i % PALETTE.length],
    backgroundColor: PALETTE[i % PALETTE.length],
    borderWidth: 2.5,
    pointRadius: 0,
    tension: 0.3,
  }));

  const cfg = {
    data: { labels, datasets },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: ctx => `${ctx.dataset.label}: ₹${fmtNum(ctx.parsed.y)}` } },
      },
      scales: {
        x: { grid: { display: false } },
        y: { grid: { color: LINE }, ticks: { callback: v => '₹' + (v / 1000) + 'k' } },
      },
    },
  };

  if (charts.revenue) { charts.revenue.data = cfg.data; charts.revenue.update(); }
  else charts.revenue = new Chart(document.getElementById('revenueChart'), { type: 'line', ...cfg });

  document.getElementById('revenue-legend').innerHTML = cities.map((c, i) => `
    <span><span class="swatch" style="background:${PALETTE[i % PALETTE.length]}"></span>${c}</span>
  `).join('') || '<span>No cities selected</span>';
}

function renderRestaurants() {
  const rows = raw.restaurants.filter(r => selectedCities.has(r.city)).sort((a, b) => Number(a.revenue) - Number(b.revenue));
  const empty = document.getElementById('restaurant-empty');
  const wrap = document.getElementById('restaurantChart').parentElement;
  if (rows.length === 0) { empty.hidden = false; wrap.style.display = 'none'; return; }
  empty.hidden = true; wrap.style.display = '';

  const total = rows.reduce((s, r) => s + Number(r.revenue), 0);
  const cfg = {
    data: {
      labels: rows.map(r => `${r.restaurant_name} · ${r.city}`),
      datasets: [{ data: rows.map(r => Number(r.revenue)), backgroundColor: '#e8462f', borderRadius: 4, barThickness: 16 }],
    },
    options: {
      indexAxis: 'y', responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: ctx => `₹${fmtNum(ctx.parsed.x)} · ${((ctx.parsed.x / total) * 100).toFixed(1)}% of shown` } },
      },
      scales: {
        x: { grid: { color: LINE }, ticks: { callback: v => '₹' + fmtNum(v) } },
        y: { grid: { display: false }, ticks: { autoSkip: false } },
      },
    },
  };
  if (charts.restaurant) { charts.restaurant.data = cfg.data; charts.restaurant.update(); }
  else charts.restaurant = new Chart(document.getElementById('restaurantChart'), { type: 'bar', ...cfg });
}

function renderSLA(filteredSla) {
  const byCity = {};
  filteredSla.forEach(r => {
    const delivered = Number(r.delivered_orders);
    if (!byCity[r.city]) byCity[r.city] = { w: 0, t: 0 };
    byCity[r.city].w += Number(r.p50) * delivered;
    byCity[r.city].t += delivered;
  });
  const cities = Object.entries(byCity).map(([city, v]) => ({ city, avg: v.t ? v.w / v.t : 0 })).sort((a, b) => a.avg - b.avg);
  const cfg = {
    data: { labels: cities.map(c => c.city), datasets: [{ data: cities.map(c => Math.round(c.avg * 10) / 10), backgroundColor: '#17a398', borderRadius: 4, barThickness: 12 }] },
    options: {
      indexAxis: 'y', responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => `${ctx.parsed.x} min median` } } },
      scales: { x: { grid: { color: LINE }, ticks: { callback: v => v + 'm' } }, y: { grid: { display: false }, ticks: { autoSkip: false, font: { size: 10 } } } },
    },
  };
  if (charts.sla) { charts.sla.data = cfg.data; charts.sla.update(); }
  else charts.sla = new Chart(document.getElementById('slaChart'), { type: 'bar', ...cfg });
}

function renderHourly(filteredSla) {
  const byHour = Array(24).fill(0);
  filteredSla.forEach(r => { byHour[Number(r.order_hour)] += Number(r.delivered_orders); });
  const cfg = {
    data: {
      labels: byHour.map((_, h) => h + ':00'),
      datasets: [{ data: byHour, borderColor: '#8b6bf2', backgroundColor: 'rgba(139,107,242,0.1)', fill: true, borderWidth: 2.5, pointRadius: 0, tension: 0.35 }],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => `${fmtNum(ctx.parsed.y)} delivered orders` } } },
      scales: { x: { grid: { display: false }, ticks: { autoSkip: true, maxTicksLimit: 12 } }, y: { grid: { color: LINE } } },
    },
  };
  if (charts.hour) { charts.hour.data = cfg.data; charts.hour.update(); }
  else charts.hour = new Chart(document.getElementById('hourChart'), { type: 'line', ...cfg });
}

function renderAll() {
  const filteredRevenue = getFilteredRevenue();
  const filteredSla = raw.sla.filter(r => selectedCities.has(r.city));
  renderPeriod(filteredRevenue);
  renderRevenue(filteredRevenue);
  renderRestaurants();
  renderSLA(filteredSla);
  renderHourly(filteredSla);
}

init();