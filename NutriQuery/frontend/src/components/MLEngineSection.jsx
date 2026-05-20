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
        {
            field: 'confidence_score',
            headerName: 'Confidence',
            width: 120,
            valueFormatter: params => params.value != null ? (params.value * 100).toFixed(1) + '%' : '--'
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
        if (data.error) setStatusMessage(`Error: ${data.error}`);
        else setStatusMessage(`${data.message} (Model Trained)`);
    };

    const clearPredictions = async () => {
        const data = await fetchAPI('/ml/predictions', { method: 'DELETE' });
        if (data.error) setStatusMessage(`Error: ${data.error}`);
        else {
            setStatusMessage(data.message);
            setPredictions([]);
        }
    };

    const loadPredictions = async () => {
        const data = await fetchAPI('/predictions/?limit=20');
        if (data && !data.error) setPredictions(data);
    };

    return (
        <section className="matte-panel">
            <div className="section-header">
                <h2>Neural Nutrition Scoring</h2>
                <span className="device-badge">{device}</span>
            </div>
            <p className="section-description">
                Run a PyTorch classifier on food data to predict unrated Nutri-Score grades.
            </p>

            <div className="button-row">
                <button className="btn-accent" onClick={runInference}>Train & Predict</button>
                <button className="btn-danger" onClick={clearPredictions}>Flush Predictions</button>
                <button className="btn-secondary" onClick={loadPredictions}>View Predictions</button>
            </div>

            {statusMessage && <div className="status-message">{statusMessage}</div>}

            {predictions.length > 0 && (
                <div className="ag-theme-quartz grid-container">
                    <AgGridReact rowData={predictions} columnDefs={colDefs} pagination={true} paginationPageSize={10} />
                </div>
            )}
        </section>
    );
}
