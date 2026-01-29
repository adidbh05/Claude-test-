/**
 * Engineering Toolbox — Interactive calculators, section browser, load combos.
 */

const TOOLS_API = '/api';
let activeToolPanel = null;

// ============== Toolbox Panel Manager ==============

function openToolPanel(panelId) {
    document.querySelectorAll('.tool-panel').forEach(p => p.classList.remove('active'));
    const panel = document.getElementById(panelId);
    if (panel) {
        panel.classList.add('active');
        activeToolPanel = panelId;
    }
    document.getElementById('toolboxOverlay')?.classList.add('active');
}

function closeToolPanel() {
    document.querySelectorAll('.tool-panel').forEach(p => p.classList.remove('active'));
    document.getElementById('toolboxOverlay')?.classList.remove('active');
    activeToolPanel = null;
}

// ============== Section Browser ==============

async function loadSectionTypes() {
    try {
        const res = await fetch(`${TOOLS_API}/sections/types`);
        const data = await res.json();
        const sel = document.getElementById('sectionTypeSelect');
        if (sel) {
            data.types.forEach(t => {
                const opt = document.createElement('option');
                opt.value = t; opt.textContent = t;
                sel.appendChild(opt);
            });
        }
    } catch (e) { console.error('Failed to load section types', e); }
}

async function searchSections() {
    const query = document.getElementById('sectionSearchInput')?.value || '';
    const type = document.getElementById('sectionTypeSelect')?.value || '';
    const url = `${TOOLS_API}/sections/search?query=${encodeURIComponent(query)}&section_type=${encodeURIComponent(type)}`;

    try {
        const res = await fetch(url);
        const data = await res.json();
        renderSectionResults(data.results || []);
    } catch (e) { console.error('Section search failed', e); }
}

function renderSectionResults(sections) {
    const container = document.getElementById('sectionResults');
    if (!container) return;

    if (!sections.length) {
        container.innerHTML = '<div class="empty-msg">No sections found</div>';
        return;
    }

    container.innerHTML = sections.slice(0, 30).map(s => {
        const p = s.properties;
        return `
        <div class="section-card" onclick="selectSection('${s.name}')">
            <div class="section-card-header">
                <span class="section-name">${s.name}</span>
                <span class="section-type-badge">${s.type}</span>
            </div>
            <div class="section-card-props">
                ${p.h ? `<span>h=${p.h}mm</span>` : ''}
                ${p.b ? `<span>b=${p.b}mm</span>` : ''}
                ${p.A ? `<span>A=${p.A}mm²</span>` : ''}
                ${p.mass ? `<span>${p.mass}kg/m</span>` : ''}
            </div>
        </div>`;
    }).join('');
}

async function selectSection(name) {
    try {
        const res = await fetch(`${TOOLS_API}/sections/${encodeURIComponent(name)}`);
        const data = await res.json();
        showSectionDetail(data);
    } catch (e) { console.error('Failed to get section', e); }
}

function showSectionDetail(section) {
    const container = document.getElementById('sectionDetail');
    if (!container) return;

    const p = section.properties;
    const units = {
        h: 'mm', b: 'mm', tw: 'mm', tf: 'mm', r: 'mm', d: 'mm', t: 'mm', a: 'mm',
        A: 'mm²', mass: 'kg/m',
        Iy: 'mm⁴', Iz: 'mm⁴', It: 'mm⁴', Iw: 'mm⁶',
        Wpl_y: 'mm³', Wpl_z: 'mm³', Wel_y: 'mm³', Wel_z: 'mm³',
        iy: 'mm', iz: 'mm',
    };

    let rows = '';
    for (const [key, val] of Object.entries(p)) {
        const unit = units[key] || '';
        const label = key.replace(/_/g, ',').replace('Wpl', 'W_pl').replace('Wel', 'W_el');
        rows += `<tr><td>${label}</td><td>${typeof val === 'number' ? val.toLocaleString() : val}</td><td>${unit}</td></tr>`;
    }

    container.innerHTML = `
        <div class="detail-header">
            <h3>${section.name}</h3>
            <span class="section-type-badge">${section.type}</span>
        </div>
        ${section.type === 'IPE' || section.type === 'HEB' || section.type === 'HEA' ? drawISection(p) : ''}
        <table class="detail-table">
            <tr><th>Property</th><th>Value</th><th>Unit</th></tr>
            ${rows}
        </table>
        <button class="tool-btn" onclick="useSectionInChat('${section.name}')">Use in Chat</button>
    `;
    container.style.display = 'block';
}

function useSectionInChat(name) {
    const input = document.getElementById('messageInput');
    if (input) {
        input.value = `Using section ${name}: `;
        input.focus();
    }
    closeToolPanel();
}

// ============== SVG Cross-Section Viewer ==============

function drawISection(p) {
    const h = p.h || 200, b = p.b || 100, tw = p.tw || 8, tf = p.tf || 12;
    const scale = 0.8;
    const svgW = 200, svgH = 200;
    const cx = svgW / 2, cy = svgH / 2;

    const hS = h * scale * (svgH / (h * 1.3));
    const bS = b * scale * (svgW / (b * 1.5));
    const twS = tw * scale * (svgW / (b * 1.5));
    const tfS = tf * scale * (svgH / (h * 1.3));

    return `
    <div class="section-svg-container">
        <svg viewBox="0 0 ${svgW} ${svgH}" class="section-svg">
            <!-- Top flange -->
            <rect x="${cx - bS/2}" y="${cy - hS/2}" width="${bS}" height="${tfS}"
                  fill="#4a9eff" opacity="0.7" stroke="#2d6ec7" stroke-width="1"/>
            <!-- Web -->
            <rect x="${cx - twS/2}" y="${cy - hS/2 + tfS}" width="${twS}" height="${hS - 2*tfS}"
                  fill="#4a9eff" opacity="0.5" stroke="#2d6ec7" stroke-width="1"/>
            <!-- Bottom flange -->
            <rect x="${cx - bS/2}" y="${cy + hS/2 - tfS}" width="${bS}" height="${tfS}"
                  fill="#4a9eff" opacity="0.7" stroke="#2d6ec7" stroke-width="1"/>
            <!-- Dimensions -->
            <text x="${cx}" y="${cy - hS/2 - 6}" text-anchor="middle" fill="#a0aec0" font-size="10">${b}mm</text>
            <text x="${cx + bS/2 + 8}" y="${cy}" text-anchor="start" fill="#a0aec0" font-size="10" dominant-baseline="middle">${h}mm</text>
        </svg>
    </div>`;
}

// ============== Beam Calculator ==============

async function runBeamCheck() {
    const form = document.getElementById('beamCalcForm');
    if (!form) return;

    const data = {
        section_name: form.querySelector('[name="section"]').value,
        steel_grade: form.querySelector('[name="grade"]').value,
        span_mm: parseFloat(form.querySelector('[name="span"]').value) || 0,
        MEd_kNm: parseFloat(form.querySelector('[name="MEd"]').value) || 0,
        VEd_kN: parseFloat(form.querySelector('[name="VEd"]').value) || 0,
        NEd_kN: parseFloat(form.querySelector('[name="NEd"]')?.value) || 0,
        Lcr_LTB_mm: parseFloat(form.querySelector('[name="LcrLTB"]')?.value) || null,
        w_sls_kN_m: parseFloat(form.querySelector('[name="wSLS"]')?.value) || null,
    };

    if (!data.span_mm) return showToast('Enter span length', 'warning');

    try {
        const res = await fetch(`${TOOLS_API}/calc/beam`, {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        if (!res.ok) { const e = await res.json(); throw new Error(e.detail); }
        const result = await res.json();
        renderCalcResult('beamCalcResult', result);
    } catch (e) { showToast(e.message, 'error'); }
}

// ============== Column Calculator ==============

async function runColumnCheck() {
    const form = document.getElementById('columnCalcForm');
    if (!form) return;

    const data = {
        section_name: form.querySelector('[name="section"]').value,
        steel_grade: form.querySelector('[name="grade"]').value,
        NEd_kN: parseFloat(form.querySelector('[name="NEd"]').value) || 0,
        Lcr_y_mm: parseFloat(form.querySelector('[name="LcrY"]').value) || 0,
        Lcr_z_mm: parseFloat(form.querySelector('[name="LcrZ"]').value) || 0,
        buckling_curve_y: form.querySelector('[name="curveY"]')?.value || 'b',
        buckling_curve_z: form.querySelector('[name="curveZ"]')?.value || 'c',
    };

    if (!data.NEd_kN || !data.Lcr_y_mm) return showToast('Enter axial force and buckling lengths', 'warning');

    try {
        const res = await fetch(`${TOOLS_API}/calc/column`, {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        if (!res.ok) { const e = await res.json(); throw new Error(e.detail); }
        const result = await res.json();
        renderCalcResult('columnCalcResult', result);
    } catch (e) { showToast(e.message, 'error'); }
}

// ============== Bolt Calculator ==============

async function runBoltCheck() {
    const form = document.getElementById('boltCalcForm');
    if (!form) return;

    const data = {
        bolt_diameter: parseInt(form.querySelector('[name="boltDia"]').value) || 20,
        bolt_grade: form.querySelector('[name="boltGrade"]').value || '8.8',
        n_bolts: parseInt(form.querySelector('[name="nBolts"]').value) || 1,
        VEd_kN: parseFloat(form.querySelector('[name="VEd"]').value) || 0,
        FtEd_kN: parseFloat(form.querySelector('[name="FtEd"]').value) || 0,
    };

    try {
        const res = await fetch(`${TOOLS_API}/calc/bolt`, {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        if (!res.ok) { const e = await res.json(); throw new Error(e.detail); }
        const result = await res.json();
        renderCalcResult('boltCalcResult', result);
    } catch (e) { showToast(e.message, 'error'); }
}

// ============== Weld Calculator ==============

async function runWeldCheck() {
    const form = document.getElementById('weldCalcForm');
    if (!form) return;

    const data = {
        throat_mm: parseFloat(form.querySelector('[name="throat"]').value) || 0,
        length_mm: parseFloat(form.querySelector('[name="length"]').value) || 0,
        steel_grade: form.querySelector('[name="grade"]').value || 'S355',
        FEd_kN: parseFloat(form.querySelector('[name="FEd"]').value) || 0,
    };

    if (!data.throat_mm || !data.length_mm || !data.FEd_kN) return showToast('Fill all fields', 'warning');

    try {
        const res = await fetch(`${TOOLS_API}/calc/weld`, {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        if (!res.ok) { const e = await res.json(); throw new Error(e.detail); }
        const result = await res.json();
        renderCalcResult('weldCalcResult', result);
    } catch (e) { showToast(e.message, 'error'); }
}

// ============== Load Combinations ==============

let loadCases = [];

function addLoadCase() {
    const name = document.getElementById('lcName')?.value || `Load ${loadCases.length + 1}`;
    const type = document.getElementById('lcType')?.value || 'permanent';
    const category = document.getElementById('lcCategory')?.value || 'B';
    const value = parseFloat(document.getElementById('lcValue')?.value) || 0;

    loadCases.push({ name, type, category, value, favorable: false });
    renderLoadCaseList();
}

function removeLoadCase(idx) {
    loadCases.splice(idx, 1);
    renderLoadCaseList();
}

function renderLoadCaseList() {
    const container = document.getElementById('loadCaseList');
    if (!container) return;

    container.innerHTML = loadCases.map((lc, i) => `
        <div class="load-case-item">
            <span>${lc.name}</span>
            <span class="lc-type">${lc.type}</span>
            <span>${lc.value} kN/m</span>
            <button class="lc-remove" onclick="removeLoadCase(${i})"><i class="fas fa-times"></i></button>
        </div>
    `).join('');
}

async function generateCombinations() {
    if (!loadCases.length) return showToast('Add load cases first', 'warning');

    const approach = document.getElementById('lcApproach')?.value || '6.10';

    try {
        const res = await fetch(`${TOOLS_API}/loads/combinations`, {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ load_cases: loadCases, approach, include_sls: true })
        });
        if (!res.ok) { const e = await res.json(); throw new Error(e.detail); }
        const data = await res.json();
        renderCombinationsResult(data);
    } catch (e) { showToast(e.message, 'error'); }
}

function renderCombinationsResult(data) {
    const container = document.getElementById('comboResults');
    if (!container) return;

    let html = '<h4>ULS Combinations</h4>';
    if (data.uls_governing) {
        html += `<div class="governing-combo">Governing: <strong>${data.uls_governing.name}</strong> = ${data.uls_governing.value} kN/m</div>`;
    }

    html += '<table class="combo-table"><tr><th>Name</th><th>Value</th></tr>';
    (data.uls || []).forEach(c => {
        const isGov = data.uls_governing && c.value === data.uls_governing.value;
        html += `<tr class="${isGov ? 'governing-row' : ''}"><td>${c.name}</td><td>${c.value}</td></tr>`;
    });
    html += '</table>';

    if (data.sls) {
        html += '<h4>SLS Combinations</h4>';
        for (const [type, combos] of Object.entries(data.sls)) {
            html += `<p class="sls-label">${type.replace('_', ' ')}</p>`;
            combos.forEach(c => { html += `<div class="sls-combo">${c.name}: <strong>${c.value}</strong></div>`; });
        }
    }

    container.innerHTML = html;
}

// ============== National Annex ==============

async function loadNationalAnnex() {
    const code = document.getElementById('naCountrySelect')?.value;
    if (!code) return;

    try {
        const res = await fetch(`${TOOLS_API}/national-annex/${code}`);
        const data = await res.json();
        renderNationalAnnex(data);
    } catch (e) { showToast('Failed to load NA', 'error'); }
}

function renderNationalAnnex(na) {
    const container = document.getElementById('naDetails');
    if (!container) return;

    const sf = na.safety_factors || {};
    const lc = na.load_combination || {};
    const bk = na.buckling || {};
    const dl = na.deflection_limits || {};

    container.innerHTML = `
        <h4>${na.country_name}</h4>
        <table class="detail-table">
            <tr><th colspan="2">Partial Safety Factors</th></tr>
            <tr><td>γM0</td><td>${sf.gamma_M0}</td></tr>
            <tr><td>γM1</td><td>${sf.gamma_M1}</td></tr>
            <tr><td>γM2</td><td>${sf.gamma_M2}</td></tr>
            <tr><th colspan="2">Load Combination</th></tr>
            <tr><td>Approach</td><td>${lc.approach}</td></tr>
            <tr><td>ξ factor</td><td>${lc.xi}</td></tr>
            <tr><td>γG,unfav</td><td>${lc.gamma_G_unfav}</td></tr>
            <tr><th colspan="2">Buckling</th></tr>
            <tr><td>LTB Method</td><td>${bk.ltb_method}</td></tr>
            <tr><th colspan="2">Deflection Limits</th></tr>
            <tr><td>Variable</td><td>${dl.variable}</td></tr>
        </table>
        <p class="na-notes">${na.notes || ''}</p>
    `;
}

async function loadNACountries() {
    try {
        const res = await fetch(`${TOOLS_API}/national-annex/countries`);
        const countries = await res.json();
        const sel = document.getElementById('naCountrySelect');
        if (sel) {
            countries.forEach(c => {
                const opt = document.createElement('option');
                opt.value = c.code; opt.textContent = `${c.code} — ${c.name}`;
                sel.appendChild(opt);
            });
        }
    } catch (e) { console.error('Failed to load NA countries', e); }
}

// ============== Result Rendering ==============

function renderCalcResult(containerId, result) {
    const container = document.getElementById(containerId);
    if (!container) return;

    let html = '';

    // Utilization gauge
    const utils = result.utilizations || {};
    const maxUtil = result.max_utilization || 0;
    const status = result.overall_status || 'OK';

    html += `<div class="result-status ${status.toLowerCase()}">${status} — ${(maxUtil * 100).toFixed(1)}%</div>`;

    // Utilization bars
    html += '<div class="util-bars">';
    for (const [name, ratio] of Object.entries(utils)) {
        const pct = Math.min(ratio * 100, 100);
        const color = ratio <= 0.5 ? '#4ade80' : ratio <= 0.75 ? '#fbbf24' : ratio <= 1.0 ? '#fb923c' : '#f87171';
        html += `
        <div class="util-bar-row">
            <span class="util-label">${name.replace(/_/g, ' ')}</span>
            <div class="util-track"><div class="util-fill" style="width:${pct}%;background:${color}"></div></div>
            <span class="util-value">${(ratio * 100).toFixed(1)}%</span>
        </div>`;
    }
    html += '</div>';

    // Key results
    const keyResults = [];
    if (result.bending) keyResults.push(['Mc,Rd', `${result.bending.Mc_Rd_kNm} kNm`]);
    if (result.shear) keyResults.push(['Vpl,Rd', `${result.shear.Vpl_Rd_kN} kN`]);
    if (result.ltb) keyResults.push(['Mb,Rd', `${result.ltb.Mb_Rd_kNm} kNm`, 'χLT=' + result.ltb.chi_LT]);
    if (result.compression) keyResults.push(['Nc,Rd', `${result.compression.Nc_Rd_kN} kN`]);
    if (result.buckling_y) keyResults.push(['Nb,Rd(y)', `${result.buckling_y.Nb_Rd_kN} kN`, 'χ=' + result.buckling_y.chi]);
    if (result.buckling_z) keyResults.push(['Nb,Rd(z)', `${result.buckling_z.Nb_Rd_kN} kN`, 'χ=' + result.buckling_z.chi]);
    if (result.classification) keyResults.push(['Section Class', result.classification.overall_class]);

    // Bolt / weld results
    if (result.shear?.Fv_Rd_kN) keyResults.push(['Fv,Rd', `${result.shear.Fv_Rd_kN || result.shear.Fv_Rd_per_bolt_kN} kN`]);
    if (result.tension) keyResults.push(['Ft,Rd', `${result.tension.Ft_Rd_kN} kN`]);
    if (result.Fw_Rd_kN) keyResults.push(['Fw,Rd', `${result.Fw_Rd_kN} kN`]);

    if (keyResults.length) {
        html += '<div class="key-results"><h4>Key Results</h4><table class="detail-table">';
        keyResults.forEach(([label, val, extra]) => {
            html += `<tr><td>${label}</td><td>${val}${extra ? ' <span class="extra">(' + extra + ')</span>' : ''}</td></tr>`;
        });
        html += '</table></div>';
    }

    // Export buttons
    html += `<div class="result-actions">
        <button class="tool-btn small" onclick="exportToChat('${containerId}')">Send to Chat</button>
    </div>`;

    container.innerHTML = html;
    container.style.display = 'block';
}

function exportToChat(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    const text = container.innerText.replace(/\n{3,}/g, '\n\n');
    const input = document.getElementById('messageInput');
    if (input) {
        input.value = `Please review these calculation results:\n${text}`;
        input.focus();
    }
    closeToolPanel();
}

// ============== Init ==============

document.addEventListener('DOMContentLoaded', () => {
    loadSectionTypes();
    loadNACountries();
});
