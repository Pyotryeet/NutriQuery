import React, { useState, useEffect } from 'react';
import { fetchAPI } from '../api';
import { AgGridReact } from 'ag-grid-react';

export default function AnalyticsSection() {
    const [minHealth, setMinHealth] = useState(50);
    const [maxSodium, setMaxSodium] = useState(200);
    const [maxCarbs, setMaxCarbs] = useState(30);
    const [noGluten, setNoGluten] = useState(false);
    const [noDairy, setNoDairy] = useState(false);
    const [categories, setCategories] = useState([]);
    const [selectedCategory, setSelectedCategory] = useState('');
    
    // Results
    const [rangeData, setRangeData] = useState([]);
    const [dietaryData, setDietaryData] = useState([]);
    const [aggData, setAggData] = useState(null);
    const [gapsData, setGapsData] = useState([]);
    
    // Column definitions for food lists
    const colDefs = [
        { field: 'fdc_id', headerName: 'ID', width: 100 },
        { field: 'food_name', headerName: 'Name', flex: 1 },
        { field: 'food_category', headerName: 'Category', flex: 1 },
        { field: 'brand_name', headerName: 'Brand', flex: 1 }
    ];

    useEffect(() => {
        const loadCategories = async () => {
            const data = await fetchAPI('/categories/');
            if (Array.isArray(data)) setCategories(data);
        };
        loadCategories();
    }, []);

    const processFoodData = (data) => {
        if (data.error || !Array.isArray(data)) return [];
        return data.map(item => ({
            fdc_id: item.fdc_id,
            food_name: item.food_name,
            food_category: item.food_category,
            brand_name: item.brand?.brand_name || ''
        }));
    };

    const runRangeQuery = async () => {
        const params = new URLSearchParams({ min_health_score: minHealth, max_sodium: maxSodium, max_carbs: maxCarbs });
        const data = await fetchAPI(`/queries/range?${params.toString()}`);
        setRangeData(processFoodData(data));
    };

    const runDietaryFilter = async () => {
        const params = new URLSearchParams({ no_gluten: noGluten, no_dairy: noDairy });
        const data = await fetchAPI(`/queries/dietary?${params.toString()}`);
        setDietaryData(processFoodData(data));
    };

    const runAggregation = async () => {
        if (!selectedCategory) return;
        const data = await fetchAPI(`/queries/aggregation?category=${encodeURIComponent(selectedCategory)}`);
        if (!data.error) setAggData(data);
    };

    const loadGaps = async () => {
        const data = await fetchAPI('/queries/gaps');
        setGapsData(processFoodData(data));
    };

    return (
        <section className="matte-panel">
            <h2>📊 Nutrition Analytics & Filters</h2>

            {/* Range Query */}
            <div className="sub-panel" style={{ marginBottom: '2rem', padding: '1.5rem', background: 'var(--bg-color)', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
                <h3>Range Query (Req 4)</h3>
                <div className="form-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', margin: '1rem 0' }}>
                    <div className="form-group">
                        <label>Min Health Score: {minHealth}</label>
                        <input type="range" min="0" max="100" value={minHealth} onChange={e => setMinHealth(e.target.value)} style={{ width: '100%' }} />
                    </div>
                    <div className="form-group">
                        <label>Max Sodium (mg)</label>
                        <input type="number" value={maxSodium} onChange={e => setMaxSodium(e.target.value)} />
                    </div>
                    <div className="form-group">
                        <label>Max Carbs (g)</label>
                        <input type="number" value={maxCarbs} onChange={e => setMaxCarbs(e.target.value)} />
                    </div>
                </div>
                <button className="btn-primary" onClick={runRangeQuery}>Execute Range Query</button>
                {rangeData.length > 0 && (
                    <div className="ag-theme-quartz" style={{ height: 250, marginTop: '1rem' }}>
                        <AgGridReact rowData={rangeData} columnDefs={colDefs} />
                    </div>
                )}
            </div>

            {/* Dietary Filtering */}
            <div className="sub-panel" style={{ marginBottom: '2rem', padding: '1.5rem', background: 'var(--bg-color)', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
                <h3>Dietary Filtering (Req 5)</h3>
                <div style={{ display: 'flex', gap: '2rem', margin: '1rem 0' }}>
                    <label>
                        <input type="checkbox" checked={noGluten} onChange={e => setNoGluten(e.target.checked)} /> Gluten-Free
                    </label>
                    <label>
                        <input type="checkbox" checked={noDairy} onChange={e => setNoDairy(e.target.checked)} /> Dairy-Free
                    </label>
                </div>
                <button className="btn-primary" onClick={runDietaryFilter}>Filter Foods</button>
                {dietaryData.length > 0 && (
                    <div className="ag-theme-quartz" style={{ height: 250, marginTop: '1rem' }}>
                        <AgGridReact rowData={dietaryData} columnDefs={colDefs} />
                    </div>
                )}
            </div>

            {/* Category Aggregation */}
            <div className="sub-panel" style={{ marginBottom: '2rem', padding: '1.5rem', background: 'var(--bg-color)', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
                <h3>Category Aggregation (Req 6)</h3>
                <div className="controls-row">
                    <div className="input-group">
                        <label>Food Category</label>
                        <select value={selectedCategory} onChange={e => setSelectedCategory(e.target.value)} style={{ width: '100%', padding: '0.75rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                            <option value="">Select a category...</option>
                            {categories.map(c => <option key={c} value={c}>{c}</option>)}
                        </select>
                    </div>
                    <button className="btn-primary" onClick={runAggregation} style={{ alignSelf: 'flex-end' }}>Aggregate</button>
                </div>
                {aggData && (
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '1rem', marginTop: '1rem', textAlign: 'center' }}>
                        <div style={{ padding: '1rem', background: '#fff', border: '1px solid var(--border-color)', borderRadius: '8px' }}><strong>{aggData.item_count}</strong><br/>Items</div>
                        <div style={{ padding: '1rem', background: '#fff', border: '1px solid var(--border-color)', borderRadius: '8px' }}><strong>{aggData.avg_calories}</strong><br/>Avg Calories</div>
                        <div style={{ padding: '1rem', background: '#fff', border: '1px solid var(--border-color)', borderRadius: '8px' }}><strong>{aggData.avg_protein}g</strong><br/>Avg Protein</div>
                        <div style={{ padding: '1rem', background: '#fff', border: '1px solid var(--border-color)', borderRadius: '8px' }}><strong>{aggData.avg_fat}g</strong><br/>Avg Fat</div>
                        <div style={{ padding: '1rem', background: '#fff', border: '1px solid var(--border-color)', borderRadius: '8px' }}><strong>{aggData.avg_carbs}g</strong><br/>Avg Carbs</div>
                    </div>
                )}
            </div>

            {/* Gaps */}
            <div className="sub-panel" style={{ padding: '1.5rem', background: 'var(--bg-color)', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
                <h3>Gap Identification (Req 7)</h3>
                <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem' }}>Find food records with incomplete nutritional data.</p>
                <button className="btn-primary" onClick={loadGaps}>Identify Gaps</button>
                {gapsData.length > 0 && (
                    <div className="ag-theme-quartz" style={{ height: 250, marginTop: '1rem' }}>
                        <AgGridReact rowData={gapsData} columnDefs={colDefs} />
                    </div>
                )}
            </div>
        </section>
    );
}
