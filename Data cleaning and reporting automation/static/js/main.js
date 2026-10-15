/**
 * AutoCleanPro Main Application Script
 */

let currentSession = null;
let customRulesState = {
    remove_duplicates: true,
    trim_whitespace: true,
    text_casing: 'none',
    missing_value_rules: {},
    outlier_rules: {},
    type_conversions: {},
    columns_to_drop: []
};

document.addEventListener('DOMContentLoaded', () => {
    initDropZone();
    initTabs();
    loadHistory();
});

// Dropzone & File Upload Logic
function initDropZone() {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');

    if (!dropZone || !fileInput) return;

    dropZone.addEventListener('click', () => fileInput.click());

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
        }, false);
    });

    dropZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0) {
            handleFileUpload(files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (fileInput.files.length > 0) {
            handleFileUpload(fileInput.files[0]);
        }
    });
}

function handleFileUpload(file) {
    const formData = new FormData();
    formData.append('file', file);
    uploadDataset(formData);
}

function loadSampleDataset(sampleName) {
    const formData = new FormData();
    formData.append('sample_name', sampleName);
    uploadDataset(formData);
}

function uploadDataset(formData) {
    showLoading('Analyzing dataset quality & structure...');

    fetch('/api/upload', {
        method: 'POST',
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        hideLoading();
        if (data.error) {
            alert('Error: ' + data.error);
            return;
        }
        currentSession = data;
        renderDashboardUploadSuccess(data);
    })
    .catch(err => {
        hideLoading();
        alert('Upload failed: ' + err);
    });
}

// Render Dashboard Data after Upload
function renderDashboardUploadSuccess(data) {
    // Show Dashboard Sections
    document.getElementById('upload-section').style.display = 'none';
    document.getElementById('dashboard-container').style.display = 'block';

    const raw = data.raw_analysis;
    const summary = raw.summary;

    // Set Header Info
    document.getElementById('dataset-filename').innerText = data.filename;
    document.getElementById('dataset-dims').innerText = `${data.total_rows} Rows × ${data.total_cols} Columns`;

    // Set Cards
    document.getElementById('card-score').innerText = `${summary.quality_score}%`;
    document.getElementById('card-grade').innerText = summary.grade;
    document.getElementById('card-rows').innerText = summary.total_rows;
    document.getElementById('card-missing').innerText = raw.missing_values.total_missing_cells;
    document.getElementById('card-duplicates').innerText = raw.duplicates.duplicate_rows_count;

    // Render Quality Gauge Chart
    Charts.renderQualityGauge('raw-score-gauge', summary.quality_score, "Initial Quality Score");

    // Render Missing Chart & Heatmap
    Charts.renderMissingChart('missing-values-chart', raw.missing_values.missing_pct_by_col);
    Charts.renderCorrelationHeatmap('correlation-heatmap', data.correlation);

    // Populate Custom Clean Controls
    populateCustomCleanRulesUI(data.columns, raw);

    // Render Preview Table
    renderTable('raw-preview-table', data.columns, data.preview_data);

    // Render Issues Detail Table
    renderIssuesTable(raw);

    // Render Summary Stats Table
    renderStatsTable(data.summary_statistics);

    // Auto switch to Overview tab
    switchTab('overview');
}

// Data Cleaning Pipeline Invocation
function triggerAutoClean() {
    if (!currentSession) return;
    executeCleaning('auto', {});
}

function triggerCustomClean() {
    if (!currentSession) return;
    // Build state from UI inputs
    buildCustomRulesFromUI();
    executeCleaning('custom', customRulesState);
}

function executeCleaning(mode, rules) {
    showLoading('Running automated data cleaning pipeline...');

    fetch('/api/clean', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            session_id: currentSession.session_id,
            mode: mode,
            rules: rules
        })
    })
    .then(res => res.json())
    .then(data => {
        hideLoading();
        if (data.error) {
            alert('Cleaning Error: ' + data.error);
            return;
        }

        renderCleaningSuccess(data);
    })
    .catch(err => {
        hideLoading();
        alert('Cleaning request failed: ' + err);
    });
}

function renderCleaningSuccess(data) {
    const rawScore = data.raw_analysis.summary.quality_score;
    const cleanScore = data.cleaned_analysis.summary.quality_score;

    // Update Comparison Cards
    document.getElementById('comparison-banner').style.display = 'flex';
    document.getElementById('raw-score-banner').innerText = `${rawScore}%`;
    document.getElementById('cleaned-score-banner').innerText = `${cleanScore}%`;

    const diff = (cleanScore - rawScore).toFixed(1);
    document.getElementById('improvement-banner').innerText = diff >= 0 ? `+${diff}%` : `${diff}%`;

    // Render Post-Cleaning Score Gauge
    Charts.renderQualityGauge('cleaned-score-gauge', cleanScore, "Post-Cleaning Score");

    // Populate Pipeline Log
    const logContainer = document.getElementById('cleaning-log-list');
    logContainer.innerHTML = '';
    data.cleaning_actions.forEach(act => {
        const li = document.createElement('li');
        li.className = 'log-item';
        li.innerHTML = `<span>⚡</span> <span>${act}</span>`;
        logContainer.appendChild(li);
    });

    // Update Tables
    renderTable('cleaned-preview-table', currentSession.columns, data.cleaned_preview);
    renderStatsTable(data.summary_statistics);

    // Update Download Links
    document.getElementById('btn-download-csv').href = data.download_urls.csv;
    document.getElementById('btn-download-xlsx').href = data.download_urls.xlsx;
    document.getElementById('btn-download-pdf').href = data.download_urls.pdf;
    document.getElementById('downloads-section').style.display = 'block';

    // Refresh History list
    loadHistory();

    // Switch to Comparison tab
    switchTab('comparison');
}

// UI Controls Population for Custom Cleaning
function populateCustomCleanRulesUI(columns, rawAnalysis) {
    const container = document.getElementById('column-rules-container');
    if (!container) return;

    container.innerHTML = '';

    columns.forEach(col => {
        const isNum = rawAnalysis.col_dtypes[col] && (rawAnalysis.col_dtypes[col].includes('int') || rawAnalysis.col_dtypes[col].includes('float'));
        const missCnt = rawAnalysis.missing_values.cols_with_missing[col] || 0;
        const outCnt = (rawAnalysis.outliers.by_column[col] || {}).count || 0;

        const row = document.createElement('div');
        row.className = 'rule-row';
        row.style.cssText = 'background:#f8fafc; padding:12px; border-radius:8px; margin-bottom:10px; border:1px solid #e2e8f0;';

        row.innerHTML = `
            <div style="font-weight:600; margin-bottom:6px;">Column: ${col} <span class="badge badge-info">${rawAnalysis.col_dtypes[col]}</span></div>
            <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap:10px;">
                <div>
                    <label style="font-size:0.8rem; font-weight:600;">Missing Strategy (${missCnt} missing):</label>
                    <select class="form-select rule-missing" data-col="${col}">
                        <option value="none">None (Keep)</option>
                        <option value="mean" ${isNum ? 'selected' : ''}>Impute Mean</option>
                        <option value="median">Impute Median</option>
                        <option value="mode" ${!isNum ? 'selected' : ''}>Impute Mode</option>
                        <option value="drop_row">Drop Rows</option>
                    </select>
                </div>
                <div>
                    <label style="font-size:0.8rem; font-weight:600;">Outlier Strategy (${outCnt} outliers):</label>
                    <select class="form-select rule-outlier" data-col="${col}" ${!isNum ? 'disabled' : ''}>
                        <option value="none">None (Keep)</option>
                        <option value="clip" selected>Clip / Winsorize (IQR)</option>
                        <option value="drop">Drop Outlier Rows</option>
                        <option value="median">Replace with Median</option>
                    </select>
                </div>
                <div>
                    <label style="font-size:0.8rem; font-weight:600;">Data Type Cast:</label>
                    <select class="form-select rule-type" data-col="${col}">
                        <option value="keep" selected>Keep Current (${rawAnalysis.col_dtypes[col]})</option>
                        <option value="numeric">Force Numeric</option>
                        <option value="datetime">Force Datetime</option>
                        <option value="string">Force String</option>
                    </select>
                </div>
            </div>
        `;
        container.appendChild(row);
    });
}

function buildCustomRulesFromUI() {
    customRulesState.remove_duplicates = document.getElementById('check-remove-dup').checked;
    customRulesState.trim_whitespace = document.getElementById('check-trim-whitespace').checked;
    customRulesState.text_casing = document.getElementById('select-casing').value;

    const missingRules = {};
    document.querySelectorAll('.rule-missing').forEach(sel => {
        missingRules[sel.dataset.col] = { strategy: sel.value };
    });
    customRulesState.missing_value_rules = missingRules;

    const outlierRules = {};
    document.querySelectorAll('.rule-outlier').forEach(sel => {
        outlierRules[sel.dataset.col] = { strategy: sel.value };
    });
    customRulesState.outlier_rules = outlierRules;

    const typeConversions = {};
    document.querySelectorAll('.rule-type').forEach(sel => {
        if (sel.value !== 'keep') {
            typeConversions[sel.dataset.col] = sel.value;
        }
    });
    customRulesState.type_conversions = typeConversions;
}

// Table Rendering Helpers
function renderTable(tableId, columns, data) {
    const table = document.getElementById(tableId);
    if (!table) return;

    let html = `<thead><tr>${columns.map(c => `<th>${c}</th>`).join('')}</tr></thead><tbody>`;

    data.slice(0, 30).forEach(row => {
        html += `<tr>${columns.map(c => `<td>${row[c] !== undefined ? row[c] : ''}</td>`).join('')}</tr>`;
    });

    html += '</tbody>';
    table.innerHTML = html;
}

function renderIssuesTable(rawAnalysis) {
    const table = document.getElementById('issues-detail-table');
    if (!table) return;

    let html = `<thead><tr>
        <th>Column Name</th>
        <th>Current Type</th>
        <th>Missing Count (%)</th>
        <th>Outliers (IQR)</th>
        <th>Formatting / Invalid Issues</th>
    </tr></thead><tbody>`;

    Object.keys(rawAnalysis.col_dtypes).forEach(col => {
        const missCnt = rawAnalysis.missing_values.cols_with_missing[col] || 0;
        const missPct = rawAnalysis.missing_values.missing_pct_by_col[col] || 0;
        const outCnt = (rawAnalysis.outliers.by_column[col] || {}).count || 0;

        const invalidItems = rawAnalysis.invalid_values.filter(i => i.column === col).map(i => i.description).join('; ');

        html += `<tr>
            <td><strong>${col}</strong></td>
            <td>${rawAnalysis.col_dtypes[col]}</td>
            <td><span class="${missCnt > 0 ? 'badge badge-danger' : 'badge badge-success'}">${missCnt} (${missPct}%)</span></td>
            <td><span class="${outCnt > 0 ? 'badge badge-warning' : 'badge badge-success'}">${outCnt}</span></td>
            <td>${invalidItems || '<span class="text-muted">None</span>'}</td>
        </tr>`;
    });

    html += '</tbody>';
    table.innerHTML = html;
}

function renderStatsTable(statsList) {
    const table = document.getElementById('summary-stats-table');
    if (!table) return;

    let html = `<thead><tr>
        <th>Column</th>
        <th>Type</th>
        <th>Count</th>
        <th>Missing (%)</th>
        <th>Mean / Top</th>
        <th>Std</th>
        <th>Min</th>
        <th>Median</th>
        <th>Max</th>
        <th>Skewness</th>
    </tr></thead><tbody>`;

    statsList.forEach(s => {
        const meanOrTop = s.mean !== undefined && s.mean !== null ? s.mean : (s.top_value || 'N/A');
        html += `<tr>
            <td><strong>${s.column}</strong></td>
            <td>${s.dtype}</td>
            <td>${s.count}</td>
            <td>${s.missing_pct}%</td>
            <td>${meanOrTop}</td>
            <td>${s.std !== undefined && s.std !== null ? s.std : '-'}</td>
            <td>${s.min !== undefined && s.min !== null ? s.min : '-'}</td>
            <td>${s.median !== undefined && s.median !== null ? s.median : '-'}</td>
            <td>${s.max !== undefined && s.max !== null ? s.max : '-'}</td>
            <td>${s.skewness !== undefined && s.skewness !== null ? s.skewness : '-'}</td>
        </tr>`;
    });

    html += '</tbody>';
    table.innerHTML = html;
}

// Load Processing History Table
function loadHistory() {
    fetch('/api/history')
    .then(res => res.json())
    .then(data => {
        const table = document.getElementById('history-table');
        if (!table) return;

        if (!data.history || data.history.length === 0) {
            table.innerHTML = '<tbody><tr><td colspan="7" class="text-muted" style="text-align:center; padding:2rem;">No previous processing records found.</td></tr></tbody>';
            return;
        }

        let html = `<thead><tr>
            <th>Session ID</th>
            <th>Dataset Name</th>
            <th>Processed Time</th>
            <th>Score Before → After</th>
            <th>Rows Before → After</th>
            <th>Issues Fixed</th>
            <th>Downloads</th>
        </tr></thead><tbody>`;

        data.history.forEach(h => {
            html += `<tr>
                <td><code>${h.session_id.substring(0, 8)}...</code></td>
                <td><strong>${h.filename}</strong></td>
                <td>${h.upload_time}</td>
                <td><span class="badge badge-warning">${h.raw_score}%</span> → <span class="badge badge-success">${h.cleaned_score}%</span></td>
                <td>${h.rows_before} → ${h.rows_after}</td>
                <td><span class="badge badge-info">${h.issues_count} operations</span></td>
                <td>
                    <a href="/download/cleaned/${h.session_id}?file_format=csv" class="btn-outline" style="padding:4px 8px; font-size:0.75rem;">CSV</a>
                    <a href="/download/pdf/${h.session_id}" class="btn-outline" style="padding:4px 8px; font-size:0.75rem;">PDF</a>
                </td>
            </tr>`;
        });

        html += '</tbody>';
        table.innerHTML = html;
    });
}

// Tab Switching Helper
function initTabs() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const tabName = btn.dataset.tab;
            switchTab(tabName);
        });
    });
}

function switchTab(tabName) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.dashboard-section').forEach(s => s.classList.remove('active'));

    const targetBtn = document.querySelector(`.tab-btn[data-tab="${tabName}"]`);
    const targetSec = document.getElementById(`tab-${tabName}`);

    if (targetBtn) targetBtn.classList.add('active');
    if (targetSec) targetSec.classList.add('active');
}

function resetApp() {
    currentSession = null;
    document.getElementById('upload-section').style.display = 'block';
    document.getElementById('dashboard-container').style.display = 'none';
    document.getElementById('comparison-banner').style.display = 'none';
    document.getElementById('downloads-section').style.display = 'none';
}

function showLoading(msg = 'Processing...') {
    document.getElementById('loading-text').innerText = msg;
    document.getElementById('loading-overlay').classList.add('active');
}

function hideLoading() {
    document.getElementById('loading-overlay').classList.remove('active');
}
