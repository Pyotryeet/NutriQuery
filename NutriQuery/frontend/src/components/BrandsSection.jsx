import React, { useState } from 'react';
import { fetchAPI } from '../api';
import { AgGridReact } from 'ag-grid-react';

export default function BrandsSection() {
    const [brandName, setBrandName] = useState('');
    const [brandOwner, setBrandOwner] = useState('');
    const [ecoscore, setEcoscore] = useState('');
    const [brands, setBrands] = useState([]);
    const [message, setMessage] = useState('');

    const colDefs = [
        { field: 'brand_name', headerName: 'Brand Name', flex: 1 },
        { field: 'brand_owner', headerName: 'Owner', flex: 1 },
        { field: 'ecoscore_grade', headerName: 'EcoScore', width: 120 }
    ];

    const createBrand = async () => {
        if (!brandName) {
            setMessage('Brand name is required.');
            return;
        }
        const body = {
            brand_name: brandName,
            brand_owner: brandOwner || null,
            ecoscore_grade: ecoscore || null
        };
        const data = await fetchAPI('/brands/', { 
            method: 'POST', 
            headers: { 'Content-Type': 'application/json' }, 
            body: JSON.stringify(body) 
        });
        
        if (data.error) setMessage(`❌ Error: ${data.error}`);
        else {
            setMessage(`✅ Brand "${data.brand_name}" created!`);
            setBrandName('');
            setBrandOwner('');
            setEcoscore('');
            loadBrands();
        }
    };

    const loadBrands = async () => {
        const data = await fetchAPI('/brands/?limit=50');
        if (data && !data.error) setBrands(data);
    };

    return (
        <section className="matte-panel">
            <h2>🏷️ Brand Management (Req 8)</h2>
            
            <div style={{ display: 'flex', gap: '2rem', flexWrap: 'wrap' }}>
                {/* Create Form */}
                <div style={{ flex: '1', minWidth: '300px', padding: '1.5rem', background: 'var(--bg-color)', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
                    <h3 style={{ marginBottom: '1rem', fontSize: '1.1rem' }}>Create Brand</h3>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginBottom: '1rem' }}>
                        <div>
                            <label style={{ display: 'block', fontSize: '0.9rem', marginBottom: '0.4rem' }}>Brand Name *</label>
                            <input type="text" value={brandName} onChange={e => setBrandName(e.target.value)} />
                        </div>
                        <div>
                            <label style={{ display: 'block', fontSize: '0.9rem', marginBottom: '0.4rem' }}>Brand Owner</label>
                            <input type="text" value={brandOwner} onChange={e => setBrandOwner(e.target.value)} />
                        </div>
                        <div>
                            <label style={{ display: 'block', fontSize: '0.9rem', marginBottom: '0.4rem' }}>Ecoscore Grade</label>
                            <input type="text" value={ecoscore} onChange={e => setEcoscore(e.target.value)} />
                        </div>
                    </div>
                    <button className="btn-primary" onClick={createBrand}>Add Brand</button>
                    {message && <div style={{ marginTop: '1rem', fontSize: '0.9rem' }}>{message}</div>}
                </div>

                {/* Brands List */}
                <div style={{ flex: '1', minWidth: '300px', padding: '1.5rem', background: 'var(--bg-color)', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                        <h3 style={{ fontSize: '1.1rem' }}>Existing Brands</h3>
                        <button className="btn-primary" style={{ padding: '0.5rem 1rem', fontSize: '0.85rem' }} onClick={loadBrands}>Refresh List</button>
                    </div>
                    
                    <div className="ag-theme-quartz" style={{ height: 300 }}>
                        <AgGridReact rowData={brands} columnDefs={colDefs} pagination={true} paginationPageSize={10} />
                    </div>
                </div>
            </div>
        </section>
    );
}
