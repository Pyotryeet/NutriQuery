const API_BASE = 'http://localhost:8000';

// ── API Helper ───────────────────────────────────────
async function fetchAPI(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, options);
        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }));
            throw new Error(error.detail || `HTTP error ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        return { error: error.message };
    }
}

// ── Toast Notifications ──────────────────────────────
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    const icons = { success: '✅', error: '❌', info: 'ℹ️', warning: '⚠️' };
    toast.innerHTML = `<span>${icons[type] || ''} ${message}</span>`;
    container.appendChild(toast);
    requestAnimationFrame(() => toast.classList.add('show'));
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 400);
    }, 3500);
}

// ── Loading State ────────────────────────────────────
function setLoading(elementId, message = 'Loading...') {
    document.getElementById(elementId).innerHTML = `
        <div class="loading-indicator">
            <div class="spinner"></div>
            <span>${message}</span>
        </div>`;
}

// ── Render Helpers ───────────────────────────────────
function renderFoodCard(food) {
    const nutrition = food.nutrition;
    const health = food.health;
    const brand = food.brand;

    const nutriscoreClass = health?.nutriscore_grade
        ? `nutriscore-${health.nutriscore_grade.toLowerCase()}`
        : '';

    return `
        <div class="food-card">
            <div class="food-card-header">
                <h4>${food.food_name}</h4>
                <span class="food-id">#${food.fdc_id}</span>
            </div>
            <div class="food-card-meta">
                ${food.food_category ? `<span class="tag">${food.food_category}</span>` : ''}
                ${brand ? `<span class="tag tag-brand">${brand.brand_name}</span>` : ''}
                ${health?.nutriscore_grade ? `<span class="tag ${nutriscoreClass}">Score: ${health.nutriscore_grade}</span>` : ''}
                ${health?.nova_group ? `<span class="tag tag-nova">NOVA ${health.nova_group}</span>` : ''}
            </div>
            ${nutrition ? `
            <div class="nutrition-grid">
                <div class="nutrient"><span class="nutrient-val">${nutrition.calories ?? '—'}</span><span class="nutrient-lbl">kcal</span></div>
                <div class="nutrient"><span class="nutrient-val">${nutrition.protein_g ?? '—'}</span><span class="nutrient-lbl">Protein</span></div>
                <div class="nutrient"><span class="nutrient-val">${nutrition.fat_g ?? '—'}</span><span class="nutrient-lbl">Fat</span></div>
                <div class="nutrient"><span class="nutrient-val">${nutrition.carbs_g ?? '—'}</span><span class="nutrient-lbl">Carbs</span></div>
                <div class="nutrient"><span class="nutrient-val">${nutrition.sodium_mg ?? '—'}</span><span class="nutrient-lbl">Sodium</span></div>
            </div>` : '<p class="text-muted">No nutrition data available.</p>'}
            ${health ? `
            <div class="health-row">
                ${health.contains_gluten ? '<span class="allergen-tag warn">Contains Gluten</span>' : '<span class="allergen-tag safe">Gluten-Free</span>'}
                ${health.contains_dairy ? '<span class="allergen-tag warn">Contains Dairy</span>' : '<span class="allergen-tag safe">Dairy-Free</span>'}
                ${health.health_score != null ? `<span class="allergen-tag">Health: ${health.health_score}</span>` : ''}
            </div>` : ''}
        </div>`;
}

function renderFoodCards(foods, elementId) {
    const el = document.getElementById(elementId);
    if (!foods || foods.error) {
        el.innerHTML = `<div class="error-state">❌ ${foods?.error || 'No data'}</div>`;
        return;
    }
    if (foods.length === 0) {
        el.innerHTML = '<div class="empty-state">No results found.</div>';
        return;
    }
    el.innerHTML = `<div class="results-count">${foods.length} result${foods.length !== 1 ? 's' : ''}</div>` +
        `<div class="food-cards-grid">${foods.map(f => renderFoodCard(f)).join('')}</div>`;
}

function renderSearchResults(items, elementId) {
    const el = document.getElementById(elementId);
    if (!items || items.error) {
        el.innerHTML = `<div class="error-state">❌ ${items?.error || 'No data'}</div>`;
        return;
    }
    if (items.length === 0) {
        el.innerHTML = '<div class="empty-state">No results found.</div>';
        return;
    }
    el.innerHTML = `
        <div class="results-count">${items.length} result${items.length !== 1 ? 's' : ''}</div>
        <div class="search-results-list">
            ${items.map(item => `
                <div class="search-item" onclick="searchFoodById(${item.fdc_id})">
                    <span class="search-item-name">${item.food_name}</span>
                    <span class="search-item-meta">
                        ${item.food_category ? `<span class="tag">${item.food_category}</span>` : ''}
                        ${item.brand_name ? `<span class="tag tag-brand">${item.brand_name}</span>` : ''}
                    </span>
                    <span class="search-item-id">#${item.fdc_id}</span>
                </div>
            `).join('')}
        </div>`;
}

// ── Food Search & Retrieval ──────────────────────────
async function searchFoodById(directId) {
    const fdcId = directId || document.getElementById('fdc-search').value;
    if (!fdcId) { showToast('Please enter a valid FDC ID.', 'warning'); return; }
    setLoading('search-result', 'Retrieving food profile...');
    const data = await fetchAPI(`/foods/${fdcId}`);
    if (data.error) {
        document.getElementById('search-result').innerHTML = `<div class="error-state">❌ ${data.error}</div>`;
    } else {
        document.getElementById('search-result').innerHTML = renderFoodCard(data);
    }
}

async function searchFoodByName() {
    const name = document.getElementById('name-search').value.trim();
    if (!name) { showToast('Please enter a food name.', 'warning'); return; }
    setLoading('search-result', `Searching for "${name}"...`);
    const data = await fetchAPI(`/foods/search?name=${encodeURIComponent(name)}`);
    renderSearchResults(data, 'search-result');
}

// ── Analytics ────────────────────────────────────────
async function runRangeQuery() {
    const minHealth = document.getElementById('min-health').value;
    const maxSodium = document.getElementById('max-sodium').value;
    const maxCarbs = document.getElementById('max-carbs').value;
    setLoading('range-result', 'Executing cross-table range query...');
    const params = new URLSearchParams({ min_health_score: minHealth, max_sodium: maxSodium, max_carbs: maxCarbs });
    const data = await fetchAPI(`/queries/range?${params.toString()}`);
    renderFoodCards(data, 'range-result');
}

async function runDietaryFilter() {
    const noGluten = document.getElementById('no-gluten').checked;
    const noDairy = document.getElementById('no-dairy').checked;
    setLoading('dietary-result', 'Filtering by dietary restrictions...');
    const params = new URLSearchParams({ no_gluten: noGluten, no_dairy: noDairy });
    const data = await fetchAPI(`/queries/dietary?${params.toString()}`);
    renderFoodCards(data, 'dietary-result');
}

async function runAggregation() {
    const category = document.getElementById('category-select').value;
    if (!category) { showToast('Select a category first.', 'warning'); return; }
    setLoading('agg-result', `Aggregating data for "${category}"...`);
    const data = await fetchAPI(`/queries/aggregation?category=${encodeURIComponent(category)}`);
    if (data.error) {
        document.getElementById('agg-result').innerHTML = `<div class="error-state">❌ ${data.error}</div>`;
        return;
    }
    document.getElementById('agg-result').innerHTML = `
        <div class="agg-stats">
            <div class="agg-card"><span class="agg-val">${data.item_count}</span><span class="agg-label">Items</span></div>
            <div class="agg-card"><span class="agg-val">${data.avg_calories}</span><span class="agg-label">Avg Calories</span></div>
            <div class="agg-card"><span class="agg-val">${data.avg_protein}g</span><span class="agg-label">Avg Protein</span></div>
            <div class="agg-card"><span class="agg-val">${data.avg_fat}g</span><span class="agg-label">Avg Fat</span></div>
            <div class="agg-card"><span class="agg-val">${data.avg_carbs}g</span><span class="agg-label">Avg Carbs</span></div>
        </div>`;
}

async function loadGaps() {
    setLoading('gaps-result', 'Scanning for incomplete records...');
    const data = await fetchAPI('/queries/gaps');
    renderFoodCards(data, 'gaps-result');
}

async function loadCategories() {
    const data = await fetchAPI('/categories/');
    const select = document.getElementById('category-select');
    if (data && !data.error && Array.isArray(data)) {
        select.innerHTML = '<option value="">Select a category...</option>' +
            data.map(c => `<option value="${c}">${c}</option>`).join('');
    }
}

// ── ML Engine ────────────────────────────────────────
async function runInference() {
    setLoading('ml-result', 'Training model and running inference on MPS/CUDA/CPU...');
    const data = await fetchAPI('/ml/predict', { method: 'POST' });
    if (data.error) {
        document.getElementById('ml-result').innerHTML = `<div class="error-state">❌ ${data.error}</div>`;
    } else {
        document.getElementById('ml-result').innerHTML = `
            <div class="success-state">
                <span class="icon">✅</span> ${data.message}
                ${data.trained ? '<span class="tag nutriscore-a">Model Trained</span>' : '<span class="tag tag-nova">Random Weights</span>'}
            </div>`;
        showToast(data.message, 'success');
    }
}

async function clearPredictions() {
    const data = await fetchAPI('/ml/predictions', { method: 'DELETE' });
    if (data.error) {
        showToast(data.error, 'error');
    } else {
        document.getElementById('ml-result').innerHTML = `<div class="success-state"><span class="icon">🗑️</span> ${data.message}</div>`;
        showToast(data.message, 'info');
    }
}

async function loadPredictions() {
    setLoading('ml-result', 'Loading predictions...');
    const data = await fetchAPI('/predictions/?limit=20');
    if (!data || data.error) {
        document.getElementById('ml-result').innerHTML = `<div class="error-state">❌ ${data?.error || 'No predictions found'}</div>`;
        return;
    }
    if (data.length === 0) {
        document.getElementById('ml-result').innerHTML = '<div class="empty-state">No predictions yet. Run inference first.</div>';
        return;
    }
    document.getElementById('ml-result').innerHTML = `
        <div class="results-count">${data.length} predictions</div>
        <div class="predictions-table">
            <table>
                <thead><tr><th>FDC ID</th><th>Food</th><th>Nutri-Score</th><th>NOVA</th><th>Confidence</th></tr></thead>
                <tbody>
                    ${data.map(p => `
                        <tr>
                            <td>${p.fdc_id}</td>
                            <td>${p.food_name || '—'}</td>
                            <td><span class="tag nutriscore-${(p.predicted_nutriscore || '').toLowerCase()}">${p.predicted_nutriscore || '—'}</span></td>
                            <td>${p.predicted_nova ?? '—'}</td>
                            <td>${p.confidence_score != null ? (p.confidence_score * 100).toFixed(1) + '%' : '—'}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>`;
}

async function loadDeviceInfo() {
    const data = await fetchAPI('/ml/device');
    const badge = document.getElementById('device-badge');
    if (data && !data.error) {
        const label = data.device.toUpperCase();
        badge.textContent = `${label} Accelerated`;
    }
}

// ── Brand Management ─────────────────────────────────
async function createBrand() {
    const name = document.getElementById('brand-name').value.trim();
    if (!name) { showToast('Brand name is required.', 'warning'); return; }
    const body = {
        brand_name: name,
        brand_owner: document.getElementById('brand-owner').value.trim() || null,
        ecoscore_grade: document.getElementById('brand-ecoscore').value.trim() || null,
    };
    const data = await fetchAPI('/brands/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    if (data.error) { showToast(data.error, 'error'); return; }
    showToast(`Brand "${data.brand_name}" created!`, 'success');
    document.getElementById('brand-name').value = '';
    document.getElementById('brand-owner').value = '';
    document.getElementById('brand-ecoscore').value = '';
    loadBrands();
}

async function loadBrands() {
    setLoading('brands-result', 'Loading brands...');
    const data = await fetchAPI('/brands/?limit=50');
    if (!data || data.error) {
        document.getElementById('brands-result').innerHTML = `<div class="error-state">❌ ${data?.error || 'Failed'}</div>`;
        return;
    }
    if (data.length === 0) {
        document.getElementById('brands-result').innerHTML = '<div class="empty-state">No brands found.</div>';
        return;
    }
    document.getElementById('brands-result').innerHTML = `
        <div class="results-count">${data.length} brands</div>
        <div class="brands-grid">
            ${data.map(b => `
                <div class="brand-card">
                    <strong>${b.brand_name}</strong>
                    ${b.brand_owner ? `<span class="text-muted">${b.brand_owner}</span>` : ''}
                    ${b.ecoscore_grade ? `<span class="tag nutriscore-${b.ecoscore_grade.toLowerCase()}">Eco: ${b.ecoscore_grade}</span>` : ''}
                </div>
            `).join('')}
        </div>`;
}

// ── Data Import ──────────────────────────────────────
async function importData() {
    setLoading('import-result', 'Importing ~40,000 records from CSV files — this may take a few minutes...');
    const data = await fetchAPI('/import', { method: 'POST' });
    if (data.error) {
        document.getElementById('import-result').innerHTML = `<div class="error-state">❌ ${data.error}</div>`;
    } else {
        document.getElementById('import-result').innerHTML = `<div class="success-state"><span class="icon">✅</span> ${data.message}</div>`;
        showToast('Import complete!', 'success');
        loadCategories();
    }
}

// ── Navigation ───────────────────────────────────────
document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', e => {
        document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
        e.target.classList.add('active');
    });
});

// Allow Enter key in search inputs
document.getElementById('fdc-search')?.addEventListener('keydown', e => { if (e.key === 'Enter') searchFoodById(); });
document.getElementById('name-search')?.addEventListener('keydown', e => { if (e.key === 'Enter') searchFoodByName(); });

// ── Init ─────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    loadCategories();
    loadDeviceInfo();
});

// Spin animation
document.head.insertAdjacentHTML('beforeend', '<style>@keyframes spin { 100% { transform: rotate(360deg); } }</style>');
