import React, { useState, useEffect } from 'react';
import { fetchAPI } from '../api';
import { AgGridReact } from 'ag-grid-react';

export default function AnalyticsSection() {
    const [minHealth, setMinHealth] = useState(50);
    const [maxSodium, setMaxSodium] = useState(200);
    const [maxCarbs, setMaxCarbs] = useState(30);
    const [noGluten, setNoGluten] = useState(true);
    const [noDairy, setNoDairy] = useState(true);
    const [categories, setCategories] = useState([]);
    const [selectedCategory, setSelectedCategory] = useState('');

    const [rangeData, setRangeData] = useState([]);
    const [dietaryData, setDietaryData] = useState([]);
    const [aggData, setAggData] = useState(null);
    const [gapsData, setGapsData] = useState([]);

    // Column defs that include nutrition/health values so users can verify filters
    const rangeColDefs = [
        { field: 'fdc_id', headerName: 'ID', width: 90 },
        {
            field: 'food_name', headerName: 'Name', flex: 2, minWidth: 180,
            cellStyle: { whiteSpace: 'normal', wordBreak: 'break-word' },
            autoHeight: true, wrapText: true,
        },
        { field: 'food_category', headerName: 'Category', flex: 1 },
        {
            field: 'health_score', headerName: 'Health', width: 80,
            cellStyle: p => p.value < 60 ? { color: 'var(--danger)', fontWeight: 600 } : { color: 'var(--success)', fontWeight: 600 },
        },
        {
            field: 'nutriscore_grade', headerName: 'Grade', width: 70,
        },
        {
            field: 'calories', headerName: 'Cal', width: 70,
            valueFormatter: p => p.value != null ? Math.round(p.value) : '--',
        },
        {
            field: 'sodium_mg', headerName: 'Na (mg)', width: 85,
            valueFormatter: p => p.value != null ? Number(p.value).toFixed(0) : '--',
        },
        {
            field: 'carbs_g', headerName: 'Carbs (g)', width: 85,
            valueFormatter: p => p.value != null ? Number(p.value).toFixed(1) : '--',
        },
    ];

    const dietaryColDefs = [
        { field: 'fdc_id', headerName: 'ID', width: 90 },
        {
            field: 'food_name', headerName: 'Name', flex: 2, minWidth: 180,
            cellStyle: { whiteSpace: 'normal', wordBreak: 'break-word' },
            autoHeight: true, wrapText: true,
        },
        { field: 'food_category', headerName: 'Category', flex: 1 },
        {
            field: 'gluten', headerName: 'Gluten', width: 80,
            cellStyle: p => p.value ? { color: 'var(--danger)' } : { color: 'var(--success)' },
            valueFormatter: p => p.value ? 'Yes' : 'No',
        },
        {
            field: 'dairy', headerName: 'Dairy', width: 80,
            cellStyle: p => p.value ? { color: 'var(--danger)' } : { color: 'var(--success)' },
            valueFormatter: p => p.value ? 'Yes' : 'No',
        },
    ];

    const gapsColDefs = [
        { field: 'fdc_id', headerName: 'ID', width: 90 },
        {
            field: 'food_name', headerName: 'Name', flex: 2, minWidth: 180,
            cellStyle: { whiteSpace: 'normal', wordBreak: 'break-word' },
            autoHeight: true, wrapText: true,
        },
        { field: 'food_category', headerName: 'Category', flex: 1 },
        {
            field: 'calories', headerName: 'Cal', width: 70,
            cellStyle: p => p.value == null ? { color: 'var(--danger)', fontWeight: 600 } : null,
            valueFormatter: p => p.value != null ? Math.round(p.value) : 'MISSING',
        },
        {
            field: 'protein_g', headerName: 'Prot', width: 70,
            cellStyle: p => p.value == null ? { color: 'var(--danger)', fontWeight: 600 } : null,
            valueFormatter: p => p.value != null ? Number(p.value).toFixed(1) : 'MISSING',
        },
        {
            field: 'fat_g', headerName: 'Fat', width: 70,
            cellStyle: p => p.value == null ? { color: 'var(--danger)', fontWeight: 600 } : null,
            valueFormatter: p => p.value != null ? Number(p.value).toFixed(1) : 'MISSING',
        },
        {
            field: 'carbs_g', headerName: 'Carbs', width: 75,
            cellStyle: p => p.value == null ? { color: 'var(--danger)', fontWeight: 600 } : null,
            valueFormatter: p => p.value != null ? Number(p.value).toFixed(1) : 'MISSING',
        },
        {
            field: 'sodium_mg', headerName: 'Na', width: 70,
            cellStyle: p => p.value == null ? { color: 'var(--danger)', fontWeight: 600 } : null,
            valueFormatter: p => p.value != null ? Number(p.value).toFixed(0) : 'MISSING',
        },
    ];

    useEffect(() => {
        const loadCategories = async () => {
            const data = await fetchAPI('/categories/');
            if (Array.isArray(data)) setCategories(data);
        };
        loadCategories();
    }, []);

    const runRangeQuery = async () => {
        const params = new URLSearchParams({ min_health_score: minHealth, max_sodium: maxSodium, max_carbs: maxCarbs });
        const data = await fetchAPI(`/queries/range?${params.toString()}`);
        if (data.error || !Array.isArray(data)) { setRangeData([]); return; }
        setRangeData(data.map(item => ({
            fdc_id: item.fdc_id,
            food_name: item.food_name,
            food_category: item.food_category,
            health_score: item.health_score?.health_score,
            nutriscore_grade: item.health_score?.nutriscore_grade,
            calories: item.nutrition?.calories,
            sodium_mg: item.nutrition?.sodium_mg,
            carbs_g: item.nutrition?.carbs_g,
        })));
    };

    const runDietaryFilter = async () => {
        const params = new URLSearchParams({ no_gluten: noGluten, no_dairy: noDairy });
        const data = await fetchAPI(`/queries/dietary?${params.toString()}`);
        if (data.error || !Array.isArray(data)) { setDietaryData([]); return; }
        setDietaryData(data.map(item => ({
            fdc_id: item.fdc_id,
            food_name: item.food_name,
            food_category: item.food_category,
            gluten: item.allergen?.contains_gluten ?? null,
            dairy: item.allergen?.contains_dairy ?? null,
        })));
    };

    const runAggregation = async () => {
        if (!selectedCategory) return;
        const data = await fetchAPI(`/queries/aggregation?category=${encodeURIComponent(selectedCategory)}`);
        if (!data.error) setAggData(data);
    };

    const loadGaps = async () => {
        const data = await fetchAPI('/queries/gaps');
        if (data.error || !Array.isArray(data)) { setGapsData([]); return; }
        setGapsData(data.map(item => ({
            fdc_id: item.fdc_id,
            food_name: item.food_name,
            food_category: item.food_category,
            calories: item.nutrition?.calories ?? null,
            protein_g: item.nutrition?.protein_g ?? null,
            fat_g: item.nutrition?.fat_g ?? null,
            carbs_g: item.nutrition?.carbs_g ?? null,
            sodium_mg: item.nutrition?.sodium_mg ?? null,
        })));
    };

    return (
        <section className="matte-panel">
            <h2>Nutrition Analytics & Filters</h2>

            {/* Range Query */}
            <div className="sub-panel">
                <h3>Range Query (Req 4)</h3>
                <p className="section-description">Filter foods by health score, sodium, and carb thresholds. Results show the actual values.</p>
                <div className="form-grid">
                    <div className="form-group">
                        <label>Min Health Score: <strong>{minHealth}</strong></label>
                        <input type="range" min="0" max="100" value={minHealth} onChange={e => setMinHealth(e.target.value)} />
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
                    <div className="ag-theme-quartz grid-container-sm">
                        <AgGridReact rowData={rangeData} columnDefs={rangeColDefs} />
                    </div>
                )}
            </div>

            {/* Dietary Filtering */}
            <div className="sub-panel">
                <h3>Dietary Filtering (Req 5)</h3>
                <p className="section-description">Find gluten-free and dairy-free foods. Results show allergen status for verification.</p>
                <div className="checkbox-row">
                    <label><input type="checkbox" checked={noGluten} onChange={e => setNoGluten(e.target.checked)} /> Gluten-Free</label>
                    <label><input type="checkbox" checked={noDairy} onChange={e => setNoDairy(e.target.checked)} /> Dairy-Free</label>
                </div>
                <button className="btn-primary" onClick={runDietaryFilter}>Filter Foods</button>
                {dietaryData.length > 0 && (
                    <div className="ag-theme-quartz grid-container-sm">
                        <AgGridReact rowData={dietaryData} columnDefs={dietaryColDefs} />
                    </div>
                )}
            </div>

            {/* Category Aggregation */}
            <div className="sub-panel">
                <h3>Category Aggregation (Req 6)</h3>
                <div className="controls-row">
                    <div className="input-group">
                        <label>Food Category</label>
                        <select value={selectedCategory} onChange={e => setSelectedCategory(e.target.value)}>
                            <option value="">Select a category...</option>
                            {categories.map(c => <option key={c} value={c}>{c}</option>)}
                        </select>
                    </div>
                    <button className="btn-primary" onClick={runAggregation}>Aggregate</button>
                </div>
                {aggData && (
                    <div className="stat-grid">
                        <div className="stat-card"><strong>{aggData.item_count}</strong><br/>Items</div>
                        <div className="stat-card"><strong>{aggData.avg_calories}</strong><br/>Avg Calories</div>
                        <div className="stat-card"><strong>{aggData.avg_protein}g</strong><br/>Avg Protein</div>
                        <div className="stat-card"><strong>{aggData.avg_fat}g</strong><br/>Avg Fat</div>
                        <div className="stat-card"><strong>{aggData.avg_carbs}g</strong><br/>Avg Carbs</div>
                    </div>
                )}
            </div>

            {/* Gaps */}
            <div className="sub-panel">
                <h3>Gap Identification (Req 7)</h3>
                <p className="section-description">Records with incomplete nutritional data. Missing fields are highlighted.</p>
                <button className="btn-primary" onClick={loadGaps}>Identify Gaps</button>
                {gapsData.length > 0 && (
                    <div className="ag-theme-quartz grid-container-sm">
                        <AgGridReact rowData={gapsData} columnDefs={gapsColDefs} />
                    </div>
                )}
            </div>
        </section>
    );
}
