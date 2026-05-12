import React, { useState, useEffect } from 'react';
import { fetchAPI } from '../api';
import { AgGridReact } from 'ag-grid-react';

export default function MLEngineSection() {
    const [device, setDevice] = useState('Detecting device...');
    const [statusMessage, setStatusMessage] = useState('');
    const [predictions, setPredictions] = useState([]);
    
    const colDefs = [
        { field: 'fdc_id', headerName: 'FDC ID', width: 100 },
        { field: 'food_name', headerName: 'Food', flex: 1 },
        { field: 'predicted_nutriscore', headerName: 'Nutri-Score', width: 120 },
        { field: 'predicted_nova', headerName: 'NOVA', width: 100 },
        { 
            field: 'confidence_score', 
            headerName: 'Confidence', 
            width: 120,
            valueFormatter: params => params.value != null ? (params.value * 100).toFixed(1) + '%' : '—'
        }
    ];

    useEffect(() => {
        const loadDevice = async () => {
            const data = await fetchAPI('/ml/device');
            if (data && !data.error) {
                setDevice(`${data.device.toUpperCase()} Accelerated`);
            }
        };
        loadDevice();
    }, []);

    const runInference = async () => {
        setStatusMessage('Training model and running inference...');
        const data = await fetchAPI('/ml/predict', { method: 'POST' });
        if (data.error) setStatusMessage(`❌ Error: ${data.error}`);
        else setStatusMessage(`✅ ${data.message} (${data.trained ? 'Model Trained' : 'Random Weights'})`);
    };

    const clearPredictions = async () => {
        const data = await fetchAPI('/ml/predictions', { method: 'DELETE' });
        if (data.error) setStatusMessage(`❌ Error: ${data.error}`);
        else {
            setStatusMessage(`🗑️ ${data.message}`);
            setPredictions([]);
        }
    };

    const loadPredictions = async () => {
        const data = await fetchAPI('/predictions/?limit=20');
        if (data && !data.error) setPredictions(data);
    };

    return (
        <section className="matte-panel" style={{ borderColor: 'var(--accent-color)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem' }}>
                <h2>🧠 Neural Nutrition Scoring</h2>
                <span style={{ padding: '4px 12px', background: 'rgba(139, 92, 246, 0.1)', color: 'var(--accent-color)', borderRadius: '20px', fontSize: '0.85rem', fontWeight: 'bold' }}>
                    {device}
                </span>
            </div>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
                Run a PyTorch classifier on food data to predict unrated Nutri-Score grades and NOVA classifications.
            </p>

            <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
                <button className="btn-primary" style={{ backgroundColor: 'var(--accent-color)' }} onClick={runInference}>🚀 Train & Predict</button>
                <button className="btn-primary" style={{ backgroundColor: 'var(--danger)' }} onClick={clearPredictions}>🗑️ Flush Predictions</button>
                <button className="btn-primary" style={{ backgroundColor: 'var(--text-secondary)' }} onClick={loadPredictions}>📋 View Predictions</button>
            </div>

            {statusMessage && <div style={{ marginBottom: '1rem', padding: '1rem', background: 'var(--bg-color)', borderRadius: '8px' }}>{statusMessage}</div>}

            {predictions.length > 0 && (
                <div className="ag-theme-quartz" style={{ height: 400 }}>
                    <AgGridReact rowData={predictions} columnDefs={colDefs} pagination={true} paginationPageSize={10} />
                </div>
            )}
        </section>
    );
}
