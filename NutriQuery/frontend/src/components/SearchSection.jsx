import React, { useState } from 'react';
import { fetchAPI } from '../api';
import { AgGridReact } from 'ag-grid-react';
import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-quartz.css';

export default function SearchSection() {
    const [fdcId, setFdcId] = useState('');
    const [name, setName] = useState('');
    const [rowData, setRowData] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const [colDefs] = useState([
        { field: 'fdc_id', headerName: 'ID', width: 100 },
        { field: 'food_name', headerName: 'Name', flex: 1 },
        { field: 'food_category', headerName: 'Category', flex: 1 },
        { field: 'brand_name', headerName: 'Brand', flex: 1 }
    ]);

    const searchById = async () => {
        if (!fdcId) return;
        setLoading(true);
        setError(null);
        const data = await fetchAPI(`/foods/${fdcId}`);
        if (data.error) {
            setError(data.error);
            setRowData([]);
        } else {
            // Flatten brand for grid
            const row = {
                fdc_id: data.fdc_id,
                food_name: data.food_name,
                food_category: data.food_category,
                brand_name: data.brand?.brand_name || ''
            };
            setRowData([row]);
        }
        setLoading(false);
    };

    const searchByName = async () => {
        if (!name) return;
        setLoading(true);
        setError(null);
        const data = await fetchAPI(`/foods/search?name=${encodeURIComponent(name)}`);
        if (data.error) {
            setError(data.error);
            setRowData([]);
        } else {
            setRowData(data);
        }
        setLoading(false);
    };

    return (
        <section className="matte-panel">
            <div className="section-header">
                <h2>🔍 Product Registry</h2>
            </div>
            <div className="controls-row">
                <div className="input-group">
                    <label htmlFor="fdc-search">Lookup by FDC ID</label>
                    <div className="input-action">
                        <input 
                            type="number" 
                            id="fdc-search" 
                            placeholder="e.g. 167782"
                            value={fdcId}
                            onChange={e => setFdcId(e.target.value)}
                        />
                        <button className="btn-primary" onClick={searchById}>Retrieve</button>
                    </div>
                </div>
                <div className="input-group">
                    <label htmlFor="name-search">Search by Name</label>
                    <div className="input-action">
                        <input 
                            type="text" 
                            id="name-search" 
                            placeholder="e.g. Apple, Chicken..."
                            value={name}
                            onChange={e => setName(e.target.value)}
                        />
                        <button className="btn-primary" onClick={searchByName}>Search</button>
                    </div>
                </div>
            </div>

            {error && <div className="error-message">❌ {error}</div>}

            <div className="ag-theme-quartz" style={{ height: 400, width: '100%', marginTop: '1rem', border: '1px solid var(--border-color)', borderRadius: '8px', overflow: 'hidden' }}>
                <AgGridReact
                    rowData={rowData}
                    columnDefs={colDefs}
                    pagination={true}
                    paginationPageSize={10}
                    loading={loading}
                    overlayLoadingTemplate={'<span class="ag-overlay-loading-center">Loading data...</span>'}
                    overlayNoRowsTemplate={'<span style="padding: 10px;">No results found.</span>'}
                />
            </div>
        </section>
    );
}
