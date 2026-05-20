import React, { useState } from 'react';
import { fetchAPI } from '../api';
import { AgGridReact } from 'ag-grid-react';

export default function BrandsSection() {
    const [brandName, setBrandName] = useState('');
    const [brandOwner, setBrandOwner] = useState('');
    const [brands, setBrands] = useState([]);
    const [message, setMessage] = useState('');

    const colDefs = [
        { field: 'brand_name', headerName: 'Brand Name', flex: 1 },
        { field: 'brand_owner', headerName: 'Owner', flex: 1 }
    ];

    const createBrand = async () => {
        if (!brandName) {
            setMessage('Brand name is required.');
            return;
        }
        const body = {
            brand_name: brandName,
            brand_owner: brandOwner || null
        };
        const data = await fetchAPI('/brands/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });

        if (data.error) setMessage(`Error: ${data.error}`);
        else {
            setMessage(`Brand "${data.brand_name}" created!`);
            setBrandName('');
            setBrandOwner('');
            loadBrands();
        }
    };

    const loadBrands = async () => {
        const data = await fetchAPI('/brands/?limit=50');
        if (data && !data.error) setBrands(data);
    };

    return (
        <section className="matte-panel">
            <h2>Brand Management (Req 8)</h2>

            <div className="two-col">
                {/* Create Form */}
                <div className="sub-panel">
                    <h3>Create Brand</h3>
                    <div className="brand-form">
                        <div className="form-group">
                            <label>Brand Name *</label>
                            <input type="text" value={brandName} onChange={e => setBrandName(e.target.value)} />
                        </div>
                        <div className="form-group">
                            <label>Brand Owner</label>
                            <input type="text" value={brandOwner} onChange={e => setBrandOwner(e.target.value)} />
                        </div>
                    </div>
                    <button className="btn-primary" onClick={createBrand}>Add Brand</button>
                    {message && <div className="status-message">{message}</div>}
                </div>

                {/* Brands List */}
                <div className="sub-panel">
                    <div className="section-header">
                        <h3>Existing Brands</h3>
                        <button className="btn-primary" onClick={loadBrands}>Refresh List</button>
                    </div>
                    <div className="ag-theme-quartz grid-container" style={{height: '300px'}}>
                        <AgGridReact rowData={brands} columnDefs={colDefs} pagination={true} paginationPageSize={10} />
                    </div>
                </div>
            </div>
        </section>
    );
}
