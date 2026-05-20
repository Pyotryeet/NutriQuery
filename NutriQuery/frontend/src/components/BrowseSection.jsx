import React, { useState, useCallback } from 'react';
import { fetchAPI } from '../api';
import { AgGridReact } from 'ag-grid-react';
import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-quartz.css';

const PAGE_SIZE = 20;

export default function BrowseSection() {
    const [searchName, setSearchName] = useState('');
    const [rowData, setRowData] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [page, setPage] = useState(0);
    const [isBrowsing, setIsBrowsing] = useState(false);

    const [selectedFood, setSelectedFood] = useState(null);
    const [detailLoading, setDetailLoading] = useState(false);

    const [editing, setEditing] = useState(null);
    const [editForm, setEditForm] = useState({});
    const [editMessage, setEditMessage] = useState('');

    const browseColDefs = [
        { field: 'fdc_id', headerName: 'ID', width: 90, cellStyle: { fontWeight: 600 } },
        {
            field: 'food_name', headerName: 'Food Name', flex: 2, minWidth: 200,
            cellStyle: { whiteSpace: 'normal', wordBreak: 'break-word' },
            autoHeight: true, wrapText: true,
        },
        { field: 'food_category', headerName: 'Category', flex: 1, minWidth: 120 },
        { field: 'brand_name', headerName: 'Brand', flex: 1, minWidth: 120 },
        {
            field: 'calories', headerName: 'Cal', width: 75,
            valueFormatter: p => p.value != null ? Math.round(p.value) : '--',
        },
        {
            field: 'protein_g', headerName: 'Prot (g)', width: 85,
            valueFormatter: p => p.value != null ? Number(p.value).toFixed(1) : '--',
        },
        {
            field: 'fat_g', headerName: 'Fat (g)', width: 80,
            valueFormatter: p => p.value != null ? Number(p.value).toFixed(1) : '--',
        },
        {
            field: 'carbs_g', headerName: 'Carbs (g)', width: 85,
            valueFormatter: p => p.value != null ? Number(p.value).toFixed(1) : '--',
        },
        {
            field: 'sodium_mg', headerName: 'Na (mg)', width: 85,
            valueFormatter: p => p.value != null ? Number(p.value).toFixed(0) : '--',
        },
    ];

    const loadPage = useCallback(async (pageNum, searchTerm) => {
        setLoading(true);
        setError(null);
        const term = searchTerm !== undefined ? searchTerm : searchName;
        const skip = pageNum * PAGE_SIZE;
        const params = new URLSearchParams({ skip: String(skip), limit: String(PAGE_SIZE) });
        if (term && term.trim()) {
            params.append('name', term.trim());
            setIsBrowsing(false);
        } else {
            setIsBrowsing(true);
        }
        const data = await fetchAPI(`/foods/browse?${params.toString()}`);
        if (data.error) {
            setError(data.error);
            setRowData([]);
        } else {
            setRowData(data.map(item => ({
                fdc_id: item.fdc_id,
                food_name: item.food_name,
                food_category: item.food_category || '--',
                brand_name: item.brand_name || '--',
                calories: item.calories,
                protein_g: item.protein_g,
                fat_g: item.fat_g,
                carbs_g: item.carbs_g,
                sodium_mg: item.sodium_mg,
            })));
            setPage(pageNum);
        }
        setLoading(false);
    }, [searchName]);

    const loadBrowse = () => loadPage(0, '');

    const doSearch = () => {
        if (!searchName.trim()) return;
        loadPage(0, searchName.trim());
    };

    const onRowClicked = async (event) => {
        const fdcId = event.data.fdc_id;
        setDetailLoading(true);
        setEditing(null);
        setEditMessage('');
        const data = await fetchAPI(`/foods/${fdcId}`);
        if (!data.error) setSelectedFood(data);
        setDetailLoading(false);
    };

    const openEdit = (section) => {
        if (!selectedFood) return;
        setEditMessage('');
        if (section === 'nutrition') {
            if (!selectedFood.nutrition) {
                setEditMessage('Error: This food has no nutrition record to edit.');
                return;
            }
            setEditForm({
                calories: selectedFood.nutrition.calories ?? '',
                protein_g: selectedFood.nutrition.protein_g ?? '',
                fat_g: selectedFood.nutrition.fat_g ?? '',
                carbs_g: selectedFood.nutrition.carbs_g ?? '',
                sodium_mg: selectedFood.nutrition.sodium_mg ?? '',
            });
        } else if (section === 'health') {
            if (!selectedFood.health_score) {
                setEditMessage('Error: This food has no health score record to edit.');
                return;
            }
            setEditForm({
                health_score: selectedFood.health_score.health_score ?? '',
                nutriscore_grade: selectedFood.health_score.nutriscore_grade ?? '',
                nova_group: selectedFood.health_score.nova_group ?? '',
            });
        } else if (section === 'allergen') {
            setEditForm({
                contains_gluten: selectedFood.allergen?.contains_gluten ?? false,
                contains_dairy: selectedFood.allergen?.contains_dairy ?? false,
            });
        }
        setEditing(section);
    };

    const saveEdit = async () => {
        if (!selectedFood) return;
        const fdcId = selectedFood.fdc_id;
        const body = { ...editForm };
        for (const k of Object.keys(body)) {
            if (k !== 'nutriscore_grade' && k !== 'contains_gluten' && k !== 'contains_dairy' && body[k] !== '') {
                body[k] = parseFloat(body[k]);
            }
        }
        if (editing === 'allergen') {
            body.contains_gluten = !!body.contains_gluten;
            body.contains_dairy = !!body.contains_dairy;
        }

        const endpoint = `/foods/${fdcId}/${editing}`;
        const data = await fetchAPI(endpoint, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });

        if (data.error) {
            setEditMessage(`Error: ${data.error}`);
        } else {
            setEditMessage('Saved successfully.');
            setEditing(null);
            const fresh = await fetchAPI(`/foods/${fdcId}`);
            if (!fresh.error) setSelectedFood(fresh);
        }
    };

    return (
        <section className="matte-panel">
            <div className="section-header">
                <h2>Food Browser</h2>
            </div>

            <div className="controls-row">
                <div className="input-group">
                    <label htmlFor="browse-search">Search by Name</label>
                    <div className="input-action">
                        <input
                            type="text" id="browse-search"
                            placeholder="e.g. Apple, Chicken..."
                            value={searchName}
                            onChange={e => setSearchName(e.target.value)}
                            onKeyDown={e => e.key === 'Enter' && doSearch()}
                        />
                        <button className="btn-primary" onClick={doSearch}>Search</button>
                    </div>
                </div>
                <div className="input-group">
                    <label>&nbsp;</label>
                    <button className="btn-accent" onClick={loadBrowse}>Browse All Foods</button>
                </div>
            </div>

            {rowData.length > 0 && (
                <div className="pagination-row">
                    <button className="btn-primary" onClick={() => loadPage(Math.max(0, page - 1), isBrowsing ? '' : searchName)}
                            disabled={page === 0}>Previous</button>
                    <span className="page-indicator">Page {page + 1}</span>
                    <button className="btn-primary" onClick={() => loadPage(page + 1, isBrowsing ? '' : searchName)}
                            disabled={rowData.length < PAGE_SIZE}>Next</button>
                </div>
            )}

            {error && <div className="error-message">{error}</div>}

            <div className="ag-theme-quartz grid-container">
                <AgGridReact
                    rowData={rowData}
                    columnDefs={browseColDefs}
                    onRowClicked={onRowClicked}
                    loading={loading}
                    pagination={false}
                    overlayLoadingTemplate={'<span class="ag-overlay-loading-center">Loading...</span>'}
                    overlayNoRowsTemplate={'<span style="padding:10px">No foods found.</span>'}
                />
            </div>

            {detailLoading && <div className="status-message">Loading details...</div>}

            {selectedFood && !detailLoading && (
                <div className="detail-panel">
                    <div className="detail-header">
                        <h3>{selectedFood.food_name}</h3>
                        <button className="btn-secondary" onClick={() => { setSelectedFood(null); setEditing(null); }}>
                            Close
                        </button>
                    </div>

                    <div className="detail-grid">
                        <div className="detail-card">
                            <div className="detail-card-header">
                                <strong>Nutrition</strong>
                                <button className="btn-primary" onClick={() => openEdit('nutrition')}>Edit</button>
                            </div>
                            {editing === 'nutrition' ? (
                                <div className="edit-form">
                                    {[
                                        ['calories', 'Calories (kcal)'],
                                        ['protein_g', 'Protein (g)'],
                                        ['fat_g', 'Fat (g)'],
                                        ['carbs_g', 'Carbs (g)'],
                                        ['sodium_mg', 'Sodium (mg)'],
                                    ].map(([field, label]) => (
                                        <label key={field}>{label}
                                            <input type="number" step="any" value={editForm[field] ?? ''}
                                                onChange={e => setEditForm({...editForm, [field]: e.target.value})} />
                                        </label>
                                    ))}
                                    <div className="edit-actions">
                                        <button className="btn-success" onClick={saveEdit}>Save</button>
                                        <button className="btn-secondary" onClick={() => setEditing(null)}>Cancel</button>
                                    </div>
                                </div>
                            ) : selectedFood.nutrition ? (
                                <table className="detail-table"><tbody>
                                    <tr><td>Calories</td><td>{selectedFood.nutrition.calories != null ? Math.round(selectedFood.nutrition.calories) + ' kcal' : '--'}</td></tr>
                                    <tr><td>Protein</td><td>{selectedFood.nutrition.protein_g != null ? selectedFood.nutrition.protein_g + ' g' : '--'}</td></tr>
                                    <tr><td>Fat</td><td>{selectedFood.nutrition.fat_g != null ? selectedFood.nutrition.fat_g + ' g' : '--'}</td></tr>
                                    <tr><td>Carbs</td><td>{selectedFood.nutrition.carbs_g != null ? selectedFood.nutrition.carbs_g + ' g' : '--'}</td></tr>
                                    <tr><td>Sodium</td><td>{selectedFood.nutrition.sodium_mg != null ? selectedFood.nutrition.sodium_mg + ' mg' : '--'}</td></tr>
                                </tbody></table>
                            ) : <p className="text-muted">No nutrition data.</p>}
                        </div>

                        <div className="detail-card">
                            <div className="detail-card-header">
                                <strong>Health Score</strong>
                                <button className="btn-primary" onClick={() => openEdit('health')}>Edit</button>
                            </div>
                            {editing === 'health' ? (
                                <div className="edit-form">
                                    <label>Health Score (0-100)
                                        <input type="number" step="any" min="0" max="100" value={editForm.health_score ?? ''}
                                            onChange={e => setEditForm({...editForm, health_score: e.target.value})} />
                                    </label>
                                    <label>Nutri-Score Grade
                                        <select value={editForm.nutriscore_grade ?? ''}
                                            onChange={e => setEditForm({...editForm, nutriscore_grade: e.target.value})}>
                                            <option value="">--</option>
                                            {['A','B','C','D','E'].map(g => <option key={g} value={g}>{g}</option>)}
                                        </select>
                                    </label>
                                    <label>NOVA Group (1-4)
                                        <input type="number" min="1" max="4" value={editForm.nova_group ?? ''}
                                            onChange={e => setEditForm({...editForm, nova_group: e.target.value})} />
                                    </label>
                                    <div className="edit-actions">
                                        <button className="btn-success" onClick={saveEdit}>Save</button>
                                        <button className="btn-secondary" onClick={() => setEditing(null)}>Cancel</button>
                                    </div>
                                </div>
                            ) : selectedFood.health_score ? (
                                <table className="detail-table"><tbody>
                                    <tr><td>Health Score</td><td>{selectedFood.health_score.health_score != null ? selectedFood.health_score.health_score : '--'}</td></tr>
                                    <tr><td>Nutri-Score</td>
                                        <td className={`grade-${(selectedFood.health_score.nutriscore_grade || '').toLowerCase()}`}>
                                            {selectedFood.health_score.nutriscore_grade || '--'}
                                        </td></tr>
                                    <tr><td>NOVA Group</td><td>{selectedFood.health_score.nova_group != null ? selectedFood.health_score.nova_group : '--'}</td></tr>
                                </tbody></table>
                            ) : <p className="text-muted">No health score data.</p>}
                        </div>

                        <div className="detail-card">
                            <div className="detail-card-header">
                                <strong>Allergens</strong>
                                <button className="btn-primary" onClick={() => openEdit('allergen')}>Edit</button>
                            </div>
                            {editing === 'allergen' ? (
                                <div className="edit-form">
                                    <label className="checkbox-label">
                                        <input type="checkbox" checked={!!editForm.contains_gluten}
                                            onChange={e => setEditForm({...editForm, contains_gluten: e.target.checked})} />
                                        Contains Gluten
                                    </label>
                                    <label className="checkbox-label">
                                        <input type="checkbox" checked={!!editForm.contains_dairy}
                                            onChange={e => setEditForm({...editForm, contains_dairy: e.target.checked})} />
                                        Contains Dairy
                                    </label>
                                    <div className="edit-actions">
                                        <button className="btn-success" onClick={saveEdit}>Save</button>
                                        <button className="btn-secondary" onClick={() => setEditing(null)}>Cancel</button>
                                    </div>
                                </div>
                            ) : (
                                <table className="detail-table"><tbody>
                                    <tr><td>Gluten</td><td>{selectedFood.allergen?.contains_gluten ? 'Yes' : 'No'}</td></tr>
                                    <tr><td>Dairy</td><td>{selectedFood.allergen?.contains_dairy ? 'Yes' : 'No'}</td></tr>
                                </tbody></table>
                            )}
                        </div>
                    </div>

                    {selectedFood.brand && (
                        <div className="detail-meta">
                            <strong>Brand:</strong> {selectedFood.brand.brand_name}
                            {selectedFood.brand.brand_owner && <> ({selectedFood.brand.brand_owner})</>}
                            &nbsp;|&nbsp;
                            <strong>Category:</strong> {selectedFood.food_category || '--'}
                            &nbsp;|&nbsp;
                            <strong>Data Type:</strong> {selectedFood.data_type || '--'}
                        </div>
                    )}

                    {editMessage && (
                        <div className={`status-message ${editMessage.startsWith('Error') ? 'error-message' : ''}`}>
                            {editMessage}
                        </div>
                    )}
                </div>
            )}
        </section>
    );
}
