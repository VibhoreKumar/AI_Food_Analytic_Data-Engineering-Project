const COLORS = ['#e8462f', '#f2a93b', '#3987e5', '#32ad78', '#9085e9', '#d55181'];
const charts = [];
let dashboardData = {};

const root = document.documentElement;
const dateLabel = new Date().toLocaleDateString('en-IN', { year: 'numeric', month: 'short', day: 'numeric' });
document.getElementById('ticket-date').textContent = dateLabel;
document.getElementById('data-date').textContent = dateLabel;

function css(name) { return getComputedStyle(root).getPropertyValue(name).trim(); }
function chartTheme() { return { text: css('--muted'), line: css('--line') }; }
function fmtNum(n) { return new Intl.NumberFormat('en-IN').format(Math.round(n)); }
function fmtMoney(n) { return `₹${(n / 10000000).toFixed(2)} Cr`; }
function fmtPct(n) { return `${(n * 100).toFixed(1)}%`; }

async function loadJSON(name) {
  const res = await fetch(`data/${name}.json`);
  if (!res.ok) throw new Error(`Failed to load ${name}.json`);
  return res.json();
}

function registerChart(chart) { charts.push(chart); return chart; }
function baseOptions() {
  const theme = chartTheme();
  return { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { ticks: { color: theme.text }, grid: { color: theme.line } }, y: { ticks: { color: theme.text }, grid: { color: theme.line } } } };
}

function renderKpis() {
  const summary = dashboardData.summary[0];
  const revenue = dashboardData.revenue;
  const sla = dashboardData.sla;
  const totalGmv = revenue.reduce((sum, row) => sum + Number(row.gmv), 0);
  const totalOrders = revenue.reduce((sum, row) => sum + Number(row.orders), 0);
  const delivered = revenue.reduce((sum, row) => sum + Number(row.delivered_orders), 0);
  const cancelRate = 1 - delivered / totalOrders;
  const weightedAov = totalGmv / delivered;
  const weightedSla = sla.reduce((sum, row) => sum + Number(row.p50) * Number(row.delivered_orders), 0) / sla.reduce((sum, row) => sum + Number(row.delivered_orders), 0);
  const avgRating = dashboardData.restaurants.reduce((sum, row) => sum + Number(row.avg_customer_rating), 0) / dashboardData.restaurants.length;
  const stats = [
    ['gross merchandise value', fmtMoney(totalGmv), 'sampled window'],
    ['orders', fmtNum(summary.total_orders), `${fmtPct(cancelRate)} cancelled`],
    ['average order value', `₹${fmtNum(weightedAov)}`, 'delivered orders'],
    ['delivery p50', `${Math.round(weightedSla)} min`, 'weighted median'],
    ['restaurants', fmtNum(summary.total_restaurants), 'active in source'],
    ['customer rating', `${avgRating.toFixed(2)} / 5`, 'top performers'],
  ];
  document.getElementById('stat-row').innerHTML = stats.map(([label, value, note]) => `<div class="stat"><span class="stat-label">${label}</span><span class="stat-value">${value}</span><span class="stat-delta">${note}</span></div>`).join('');
  return { totalGmv, totalOrders, delivered, cancelRate, weightedAov, weightedSla, avgRating };
}

function renderRevenue() {
  const rows = dashboardData.revenue;
  const totals = {};
  rows.forEach(row => { totals[row.city] = (totals[row.city] || 0) + Number(row.gmv); });
  const topCities = Object.entries(totals).sort((a, b) => b[1] - a[1]).slice(0, 6).map(([city]) => city);
  const months = [...new Set(rows.map(row => row.month))].sort();
  const byCity = Object.fromEntries(topCities.map(city => [city, months.map(() => 0)]));
  rows.forEach(row => { if (byCity[row.city]) byCity[row.city][months.indexOf(row.month)] = Number(row.gmv); });
  const chart = registerChart(new Chart(document.getElementById('revenueChart'), { type: 'line', data: { labels: months.map(month => new Date(month).toLocaleDateString('en-IN', { month: 'short', year: '2-digit' })), datasets: topCities.map((city, i) => ({ label: city, data: byCity[city], borderColor: COLORS[i], backgroundColor: COLORS[i], borderWidth: 2, pointRadius: 0, tension: .25 })) }, options: { ...baseOptions(), scales: { x: { grid: { display: false } }, y: { grid: { color: chartTheme().line }, ticks: { callback: value => `₹${value / 1000}k` } } } } }));
  document.getElementById('revenue-legend').innerHTML = topCities.map((city, i) => `<span><span class="swatch" style="background:${COLORS[i]}"></span>${city}</span>`).join('');
  return { topCity: topCities[0], topCityRevenue: totals[topCities[0]] };
}

function renderRestaurants() {
  const sorted = dashboardData.restaurants.map(row => ({ name: row.restaurant_name, city: row.city, revenue: Number(row.revenue) })).sort((a, b) => a.revenue - b.revenue);
  return registerChart(new Chart(document.getElementById('restaurantChart'), { type: 'bar', data: { labels: sorted.map(row => `${row.name} · ${row.city}`), datasets: [{ data: sorted.map(row => row.revenue), backgroundColor: css('--chili'), borderRadius: 3, barThickness: 16 }] }, options: { ...baseOptions(), indexAxis: 'y', scales: { x: { grid: { color: chartTheme().line }, ticks: { callback: value => `₹${fmtNum(value)}` } }, y: { grid: { display: false }, ticks: { autoSkip: false } } } } }));
  return sorted[sorted.length - 1];
}

function renderSla() {
  const byCity = {};
  dashboardData.sla.forEach(row => { if (!byCity[row.city]) byCity[row.city] = { weighted: 0, total: 0 }; byCity[row.city].weighted += Number(row.p50) * Number(row.delivered_orders); byCity[row.city].total += Number(row.delivered_orders); });
  const cities = Object.entries(byCity).map(([city, value]) => ({ city, avg: value.weighted / value.total })).sort((a, b) => a.avg - b.avg);
  return registerChart(new Chart(document.getElementById('slaChart'), { type: 'bar', data: { labels: cities.map(row => row.city), datasets: [{ data: cities.map(row => Math.round(row.avg * 10) / 10), backgroundColor: css('--turmeric'), borderRadius: 3, barThickness: 12 }] }, options: { ...baseOptions(), indexAxis: 'y', scales: { x: { grid: { color: chartTheme().line }, ticks: { callback: value => `${value}m` } }, y: { grid: { display: false }, ticks: { autoSkip: false, font: { size: 10 } } } } } }));
  return cities;
}

function renderHourly() {
  const byHour = Array(24).fill(0);
  dashboardData.sla.forEach(row => { byHour[Number(row.order_hour)] += Number(row.delivered_orders); });
  const peakHour = byHour.indexOf(Math.max(...byHour));
  registerChart(new Chart(document.getElementById('hourChart'), { type: 'line', data: { labels: byHour.map((_, hour) => `${hour}:00`), datasets: [{ data: byHour, borderColor: css('--blue'), backgroundColor: 'rgba(57,135,229,.12)', fill: true, borderWidth: 2, pointRadius: 0, tension: .3 }] }, options: { ...baseOptions(), scales: { x: { grid: { display: false }, ticks: { autoSkip: true, maxTicksLimit: 12 } }, y: { grid: { color: chartTheme().line } } } } }));
  return peakHour;
}

function renderReadouts(kpis, revenueMeta, restaurant, cities, peakHour) {
  document.getElementById('insight-title').textContent = `${peakHour}:00 is the peak hour`;
  document.getElementById('insight-copy').textContent = `${revenueMeta.topCity} leads city GMV at ${fmtMoney(revenueMeta.topCityRevenue)}. The platform runs at ${Math.round(kpis.weightedSla)} minutes p50 with a ${fmtPct(kpis.cancelRate)} cancellation rate.`;
  const fastest = cities[0];
  const slowest = cities[cities.length - 1];
  document.getElementById('ops-list').innerHTML = [
    ['Fastest city', `${fastest.city} · ${Math.round(fastest.avg)} min`],
    ['Slowest city', `${slowest.city} · ${Math.round(slowest.avg)} min`],
    ['Cancellation rate', fmtPct(kpis.cancelRate)],
    ['Top restaurant', restaurant.name],
    ['Top restaurant GMV', fmtMoney(restaurant.revenue)],
  ].map(([label, value]) => `<div class="metric-item"><span>${label}</span><strong>${value}</strong></div>`).join('');
}

function setupNavigation() {
  const titles = { overview: 'The pulse of the platform', operations: 'Where the operation bends', restaurants: 'The leaderboard, by revenue' };
  document.querySelectorAll('.view-link').forEach(button => button.addEventListener('click', () => {
    const view = button.dataset.view;
    document.querySelectorAll('.view-link').forEach(item => item.classList.toggle('active', item === button));
    document.querySelectorAll('.view-panel').forEach(panel => panel.classList.toggle('active', panel.dataset.panel === view));
    document.getElementById('view-kicker').textContent = view;
    document.getElementById('view-title').textContent = titles[view];
    charts.forEach(chart => chart.resize());
  }));
}

function setupTheme() {
  const button = document.getElementById('theme-toggle');
  const saved = localStorage.getItem('zomato-theme');
  if (saved) root.dataset.theme = saved;
  button.addEventListener('click', () => {
    const next = root.dataset.theme === 'light' ? 'dark' : 'light';
    if (next === 'dark') delete root.dataset.theme; else root.dataset.theme = next;
    localStorage.setItem('zomato-theme', next);
    button.textContent = next === 'light' ? '☾' : '☼';
    button.setAttribute('aria-label', `Switch to ${next === 'light' ? 'dark' : 'light'} mode`);
    const theme = chartTheme();
    charts.forEach(chart => { chart.options.scales.x.ticks.color = theme.text; chart.options.scales.y.ticks.color = theme.text; chart.options.scales.x.grid.color = theme.line; chart.options.scales.y.grid.color = theme.line; chart.update(); });
  });
}

async function main() {
  try {
    const [summary, revenue, sla, restaurants] = await Promise.all([loadJSON('summary_stats'), loadJSON('city_revenue'), loadJSON('delivery_sla'), loadJSON('restaurant_performance')]);
    dashboardData = { summary, revenue, sla, restaurants };
    const kpis = renderKpis();
    const revenueMeta = renderRevenue();
    const restaurant = renderRestaurants();
    const cities = renderSla();
    const peakHour = renderHourly();
    renderReadouts(kpis, revenueMeta, restaurant, cities, peakHour);
    setupNavigation();
    setupTheme();
  } catch (err) {
    console.error(err);
    document.getElementById('stat-row').innerHTML = '<div class="stat"><span class="stat-label">error</span><span class="stat-value">Check data/*.json</span></div>';
  }
}

main();
