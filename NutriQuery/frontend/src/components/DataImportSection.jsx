import React, { useState } from 'react';
import { fetchAPI } from '../api';

export default function DataImportSection() {
    const [message, setMessage] = useState('');
    const [loading, setLoading] = useState(false);

    const importData = async () => {
        setLoading(true);
        setMessage('Importing records from CSV files -- this may take a few minutes...');
        const data = await fetchAPI('/import', { method: 'POST' });
        if (data.error) {
            setMessage(`Error: ${data.error}`);
        } else {
            setMessage(data.message);
        }
        setLoading(false);
    };

    return (
        <section className="matte-panel">
            <h2>Data Import (Req 1)</h2>
            <p className="section-description">
                Import food data from CSV files into the MSSQL database.
            </p>
            <button className="btn-success" onClick={importData} disabled={loading}>
                {loading ? 'Importing...' : 'Run Full Import'}
            </button>
            {message && <div className="status-message">{message}</div>}
        </section>
    );
}
