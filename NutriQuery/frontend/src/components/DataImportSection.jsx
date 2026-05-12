import React, { useState } from 'react';
import { fetchAPI } from '../api';

export default function DataImportSection() {
    const [message, setMessage] = useState('');
    const [loading, setLoading] = useState(false);

    const importData = async () => {
        setLoading(true);
        setMessage('Importing ~40,000 records from CSV files — this may take a few minutes...');
        const data = await fetchAPI('/import', { method: 'POST' });
        if (data.error) {
            setMessage(`❌ Error: ${data.error}`);
        } else {
            setMessage(`✅ ${data.message}`);
        }
        setLoading(false);
    };

    return (
        <section className="matte-panel" style={{ backgroundColor: 'var(--bg-color)', borderColor: 'var(--success)' }}>
            <h2>📥 Data Import (Req 1)</h2>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
                Import food data from CSV files into the MSSQL database. This will process ~40,000 records from USDA and OpenFoodFacts datasets.
            </p>
            <button className="btn-primary" style={{ backgroundColor: 'var(--success)', color: '#fff' }} onClick={importData} disabled={loading}>
                {loading ? '⚡ Importing...' : '⚡ Run Full Import'}
            </button>
            {message && <div style={{ marginTop: '1rem', padding: '1rem', background: '#fff', borderRadius: '8px', border: '1px solid var(--border-color)' }}>{message}</div>}
        </section>
    );
}
