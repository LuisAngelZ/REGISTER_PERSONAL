// ============ ROL DE LIBRES ============
const MAX_POR_DIA = 3;
const MESES_NOMBRE = ['ENERO','FEBRERO','MARZO','ABRIL','MAYO','JUNIO','JULIO','AGOSTO','SEPTIEMBRE','OCTUBRE','NOVIEMBRE','DICIEMBRE'];
const DIAS_SEMANA_MAP = { 0:'domingo', 1:'lunes', 2:'martes', 3:'miercoles', 4:'jueves', 5:'viernes', 6:'sabado' };
const COL_TO_DIA = ['lunes','martes','miercoles','jueves','viernes','sabado','domingo'];

let rolAssigned = {};
let _rolPersonal = [];
let _rolMes = 0;
let _rolAnio = 2026;
let _rolSaved = false;

(function() {
    const now = new Date();
    const el = document.getElementById('rolMes');
    if (el) el.value = now.getMonth();
    const el2 = document.getElementById('rolAnio');
    if (el2) el2.value = now.getFullYear();
})();

function getDatesForColumn(colIndex) {
    const lastDay = new Date(_rolAnio, _rolMes + 1, 0);
    const totalDays = lastDay.getDate();
    const dates = [];
    for (let d = 1; d <= totalDays; d++) {
        const dt = new Date(_rolAnio, _rolMes, d);
        let dow = dt.getDay();
        dow = (dow === 0) ? 6 : dow - 1;
        if (dow === colIndex) {
            dates.push(`${_rolAnio}-${String(_rolMes+1).padStart(2,'0')}-${String(d).padStart(2,'0')}`);
        }
    }
    return dates;
}

function getColFromDate(dateStr) {
    const dt = new Date(dateStr + 'T00:00:00');
    let dow = dt.getDay();
    return (dow === 0) ? 6 : dow - 1;
}

function buildRolSidebar(personal) {
    const list = document.getElementById('rolSidebarList');
    if (!personal.length) {
        list.innerHTML = '<p style="padding:12px;color:var(--slate-400);font-size:0.8rem;">Sin personal activo</p>';
        return;
    }
    list.innerHTML = personal.map(p => {
        const cargo = PUESTOS_LABEL[p.puesto] || p.puesto || '';
        const isPlaced = rolAssigned[p.id] !== undefined;
        return `<div class="rol-drag-item ${isPlaced ? 'placed' : ''}" draggable="true" data-pid="${p.id}">
            <span class="drag-handle">&#9776;</span>
            <div class="drag-name">
                ${escapeHtml(p.nombre)} ${escapeHtml(p.apellido)}
                <div class="drag-cargo">${escapeHtml(cargo)}</div>
            </div>
        </div>`;
    }).join('');

    list.querySelectorAll('.rol-drag-item:not(.placed)').forEach(item => {
        item.addEventListener('dragstart', (e) => {
            e.dataTransfer.setData('text/plain', item.dataset.pid);
            e.dataTransfer.effectAllowed = 'copy';
            item.style.opacity = '0.5';
        });
        item.addEventListener('dragend', () => {
            item.style.opacity = '1';
            document.querySelectorAll('.drag-over, .drag-over-full').forEach(el => {
                el.classList.remove('drag-over', 'drag-over-full');
            });
        });
    });
}

async function generarRolLibres() {
    _rolMes = parseInt(document.getElementById('rolMes').value);
    _rolAnio = parseInt(document.getElementById('rolAnio').value);
    const container = document.getElementById('rolCalendarContainer');

    try {
        const resp = await apiFetch(`${API_URL}/api/personal/?activos=true&limit=200`);
        if (resp.ok) _rolPersonal = await resp.json();
    } catch(e) { console.error(e); }

    // Pre-cargar asignaciones desde la BD (dia_libre guardado en cada persona)
    // Solo si el usuario no ha arrastrado nada todavia en esta sesion
    if (Object.keys(rolAssigned).length === 0) {
        _rolPersonal.forEach(p => {
            if (p.dia_libre) rolAssigned[p.id] = p.dia_libre;
        });
    }

    buildRolSidebar(_rolPersonal);

    const libresPorDia = {};
    for (const [pid, dia] of Object.entries(rolAssigned)) {
        if (!libresPorDia[dia]) libresPorDia[dia] = [];
        const person = _rolPersonal.find(p => p.id === parseInt(pid));
        if (person) libresPorDia[dia].push(person);
    }

    const firstDay = new Date(_rolAnio, _rolMes, 1);
    const lastDay = new Date(_rolAnio, _rolMes + 1, 0);
    const totalDays = lastDay.getDate();
    let startDow = firstDay.getDay();
    startDow = (startDow === 0) ? 6 : startDow - 1;

    const tituloGuardado = localStorage.getItem('rolTitulo') || 'ROL DE LIBRES "POLLITO SENSACION"';
    let html = `
        <div class="rol-title" id="rolPrintTitle">
            <h2 contenteditable="true" spellcheck="false" id="rolTituloEditable"
                style="cursor:text;outline:none;border-bottom:2px dashed transparent;"
                onfocus="this.style.borderBottomColor='var(--accent)'"
                onblur="this.style.borderBottomColor='transparent';localStorage.setItem('rolTitulo',this.textContent.trim())"
            >${tituloGuardado}</h2>
            <p>${MESES_NOMBRE[_rolMes]} &nbsp;&nbsp;&nbsp; ${_rolAnio}</p>
        </div>
        <table class="rol-calendar" id="rolTable">
            <thead>
                <tr>
                    <th>LUNES</th><th>MARTES</th><th>MIERCOLES</th><th>JUEVES</th><th>VIERNES</th><th class="weekend">SABADO</th><th class="weekend">DOMINGO</th>
                </tr>
            </thead>
            <tbody>
    `;

    let dayCount = 1;
    const weeks = Math.ceil((totalDays + startDow) / 7);

    for (let w = 0; w < weeks; w++) {
        html += '<tr>';
        for (let d = 0; d < 7; d++) {
            const cellIndex = w * 7 + d;
            if (cellIndex < startDow || dayCount > totalDays) {
                html += '<td class="empty"></td>';
            } else {
                const dateStr = `${_rolAnio}-${String(_rolMes+1).padStart(2,'0')}-${String(dayCount).padStart(2,'0')}`;
                const dowName = COL_TO_DIA[d];
                const isDomingo = d === 6;

                const peopleLibre = (libresPorDia[dowName] || []).slice(0, MAX_POR_DIA);
                const isFull = peopleLibre.length >= MAX_POR_DIA;

                const chipsHtml = peopleLibre.map(p => {
                    const cargo = PUESTOS_LABEL[p.puesto] || p.puesto || '';
                    return `<span class="rol-person-chip" data-pid="${p.id}">
                        ${escapeHtml(p.nombre)} ${escapeHtml(p.apellido)}
                        <span class="chip-cargo">${escapeHtml(cargo)}</span>
                        <span class="chip-remove" onclick="event.stopPropagation();quitarDelRol(${p.id})">&times;</span>
                    </span>`;
                }).join('');

                const fullLabel = isFull ? '<div class="rol-cell-full">COMPLETO</div>' : '';

                html += `<td data-date="${dateStr}" data-col="${d}" data-count="${peopleLibre.length}">
                    <div class="rol-day-num ${isDomingo?'domingo':''}">${dayCount}</div>
                    <div class="rol-cell-people" id="rc-${dateStr}">${chipsHtml}</div>
                    ${fullLabel}
                </td>`;
                dayCount++;
            }
        }
        html += '</tr>';
    }

    html += '</tbody></table>';
    container.innerHTML = html;

    container.querySelectorAll('td[data-date]').forEach(td => {
        td.addEventListener('dragover', (e) => {
            e.preventDefault();
            const col = parseInt(td.dataset.col);
            const diaName = COL_TO_DIA[col];
            const count = (libresPorDia[diaName] || []).length;
            if (count >= MAX_POR_DIA) {
                e.dataTransfer.dropEffect = 'none';
                highlightColumn(col, 'drag-over-full');
            } else {
                e.dataTransfer.dropEffect = 'copy';
                highlightColumn(col, 'drag-over');
            }
        });
        td.addEventListener('dragleave', (e) => {
            const related = e.relatedTarget;
            if (!td.contains(related)) {
                clearColumnHighlights();
            }
        });
        td.addEventListener('drop', (e) => {
            e.preventDefault();
            clearColumnHighlights();
            const pid = parseInt(e.dataTransfer.getData('text/plain'));
            const col = parseInt(td.dataset.col);
            if (pid) {
                agregarAlColumna(col, pid);
            }
        });
    });
}

function highlightColumn(colIndex, className) {
    clearColumnHighlights();
    document.querySelectorAll(`td[data-col="${colIndex}"]`).forEach(td => {
        td.classList.add(className);
    });
}

function clearColumnHighlights() {
    document.querySelectorAll('.drag-over, .drag-over-full').forEach(el => {
        el.classList.remove('drag-over', 'drag-over-full');
    });
}

function agregarAlColumna(colIndex, personalId) {
    const diaName = COL_TO_DIA[colIndex];

    const currentCount = Object.entries(rolAssigned).filter(([pid, dia]) => {
        return dia === diaName && _rolPersonal.find(p => p.id === parseInt(pid));
    }).length;

    if (currentCount >= MAX_POR_DIA) {
        mostrarAlerta(`Maximo ${MAX_POR_DIA} personas por dia (${diaName})`, 'error');
        return;
    }

    if (rolAssigned[personalId] === diaName) {
        mostrarAlerta('Esta persona ya tiene libre este dia', 'warning');
        return;
    }

    rolAssigned[personalId] = diaName;
    generarRolLibres();
}

function quitarDelRol(personalId) {
    delete rolAssigned[personalId];
    generarRolLibres();
}

// ========== GUARDAR SOLO ==========
async function guardarRolLibres() {
    if (Object.keys(rolAssigned).length === 0) {
        mostrarAlerta('No hay dias libres asignados para guardar', 'warning');
        return;
    }
    const updates = Object.entries(rolAssigned).map(([pid, dia]) =>
        apiFetch(`${API_URL}/api/personal/${pid}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ dia_libre: dia })
        })
    );
    try {
        await Promise.all(updates);
        _rolSaved = true;
        mostrarAlerta('Dias libres guardados correctamente', 'success');
    } catch(e) {
        mostrarAlerta('Error al guardar algunos dias libres', 'error');
    }
}

// ========== GENERAR HTML LIMPIO PARA PREVIEW E IMPRESION ==========
function generarHtmlPrevistaRol() {
    const tituloGuardado = localStorage.getItem('rolTitulo') || 'ROL DE LIBRES "POLLITO SENSACION"';

    const libresPorDia = {};
    for (const [pid, dia] of Object.entries(rolAssigned)) {
        if (!libresPorDia[dia]) libresPorDia[dia] = [];
        const person = _rolPersonal.find(p => p.id === parseInt(pid));
        if (person) libresPorDia[dia].push(person);
    }

    const firstDay = new Date(_rolAnio, _rolMes, 1);
    const lastDay  = new Date(_rolAnio, _rolMes + 1, 0);
    const totalDays = lastDay.getDate();
    let startDow = firstDay.getDay();
    startDow = (startDow === 0) ? 6 : startDow - 1;
    const weeks = Math.ceil((totalDays + startDow) / 7);

    const pca = '-webkit-print-color-adjust:exact;print-color-adjust:exact;';
    const thBase = `border:1.5px solid #555;padding:4px 2px;font-weight:700;text-align:center;font-family:Arial,sans-serif;font-size:var(--rol-font-size,9pt);${pca}`;

    let html = `
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:3mm;">
        <div style="flex:1;"></div>
        <div style="text-align:center;flex:3;">
            <div style="font-size:var(--rol-font-titulo,14pt);font-weight:bold;letter-spacing:1px;text-transform:uppercase;font-family:Arial,sans-serif;">${escapeHtml(tituloGuardado)}</div>
            <div style="font-size:var(--rol-font-subtitulo,11pt);font-weight:600;margin-top:1mm;letter-spacing:2px;font-family:Arial,sans-serif;">${MESES_NOMBRE[_rolMes]}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;${_rolAnio}</div>
        </div>
        <div style="flex:1;text-align:right;padding-right:2mm;">
            <div style="width:55px;height:45px;border:1px dashed #aaa;display:inline-flex;align-items:center;justify-content:center;font-size:6pt;color:#aaa;">LOGO</div>
        </div>
    </div>
    <table style="width:100%;border-collapse:collapse;table-layout:fixed;">
        <thead>
            <tr>
                <th class="th-wd" style="${thBase}background:#d4c5a0;">LUNES</th>
                <th class="th-wd" style="${thBase}background:#d4c5a0;">MARTES</th>
                <th class="th-wd" style="${thBase}background:#d4c5a0;">MIERCOLES</th>
                <th class="th-wd" style="${thBase}background:#d4c5a0;">JUEVES</th>
                <th class="th-wd" style="${thBase}background:#d4c5a0;">VIERNES</th>
                <th class="th-we" style="${thBase}background:#b8a878;">SABADO</th>
                <th class="th-we" style="${thBase}background:#b8a878;">DOMINGO</th>
            </tr>
        </thead>
        <tbody>`;

    let dayCount = 1;
    for (let w = 0; w < weeks; w++) {
        html += `<tr class="pv-row" style="height:var(--rol-row-height,55px);">`;
        for (let d = 0; d < 7; d++) {
            const cellIndex = w * 7 + d;
            if (cellIndex < startDow || dayCount > totalDays) {
                html += `<td class="td-empty" style="border:1px solid #bbb;background:#f0f0f0;"></td>`;
            } else {
                const dowName = COL_TO_DIA[d];
                const people  = (libresPorDia[dowName] || []).slice(0, MAX_POR_DIA);
                const isWeekend = d >= 5;
                const tdClass = isWeekend ? 'td-we' : 'td-wd';
                const bg      = isWeekend ? '#fdf9e3' : '#ffffff';

                const namesHtml = people.map(p =>
                    `<div style="border-bottom:1px solid #e0e0e0;padding:2px 4px;font-size:var(--rol-font-size,9pt);font-weight:700;text-align:center;text-transform:uppercase;font-family:Arial,sans-serif;overflow:hidden;">${escapeHtml(p.nombre)} ${escapeHtml(p.apellido)}</div>`
                ).join('');

                html += `<td class="${tdClass}" style="border:1px solid #999;vertical-align:top;background:${bg};overflow:hidden;">
                    <div style="font-size:calc(var(--rol-font-size,9pt) - 1pt);font-weight:700;border-bottom:1px solid #ccc;padding:1px 4px;color:#555;text-align:right;font-family:Arial,sans-serif;">${dayCount}</div>
                    ${namesHtml}
                </td>`;
                dayCount++;
            }
        }
        html += `</tr>`;
    }
    html += `</tbody></table>`;
    return { html, weeks };
}

// ========== VISTA PREVIA ==========
function previsualizarRol() {
    if (!_rolPersonal.length) {
        mostrarAlerta('Genera el rol primero seleccionando mes y ano', 'warning');
        return;
    }
    const { html } = generarHtmlPrevistaRol();
    const body = document.getElementById('rolPreviewBody');

    const sheet = document.createElement('div');
    sheet.id = 'rolPreviewSheet';
    sheet.style.cssText = 'background:white;width:267mm;min-height:185mm;margin:0 auto;padding:5mm 6mm;box-sizing:border-box;box-shadow:0 3px 16px rgba(0,0,0,0.45);font-family:Arial,Helvetica,sans-serif;';
    sheet.innerHTML = html;

    body.innerHTML = '';
    body.appendChild(sheet);

    ajustarAltoFila(document.getElementById('rolRowHeight').value);
    ajustarFuenteRol(document.getElementById('rolFontSize').value);

    document.getElementById('rolPreviewModal').style.display = 'flex';
}

function cerrarPreviewRol() {
    document.getElementById('rolPreviewModal').style.display = 'none';
}

// ========== SLIDERS ==========
function ajustarAltoFila(val) {
    document.getElementById('rolRowHeightVal').textContent = val;
    document.documentElement.style.setProperty('--rol-row-height', val + 'px');
    document.querySelectorAll('#rolPreviewBody .pv-row').forEach(tr => {
        tr.style.height = val + 'px';
    });
}

function ajustarFuenteRol(val) {
    document.getElementById('rolFontSizeVal').textContent = val;
    const pt = parseInt(val);
    document.documentElement.style.setProperty('--rol-font-size',      pt + 'pt');
    document.documentElement.style.setProperty('--rol-font-titulo',    (pt + 5) + 'pt');
    document.documentElement.style.setProperty('--rol-font-subtitulo', (pt + 2) + 'pt');
}

// ========== IMPRIMIR ==========
function imprimirRol() {
    if (!_rolPersonal.length) { mostrarAlerta('Genera el rol primero', 'warning'); return; }

    const { weeks, html: printHtml } = generarHtmlPrevistaRol();
    const fs = parseInt(document.getElementById('rolFontSize').value);

    // Calcular alto optimo: letter landscape 216mm - 6mm*2 margins - titulo ~18mm - header ~9mm = ~177mm
    const altoFilaMm = Math.max(20, Math.floor(177 / weeks));

    // Crear div temporal que contiene el HTML limpio para imprimir
    // Las CSS custom properties se ponen directamente en el div padre para que
    // los var() en los inline styles de los hijos las resuelvan correctamente
    const printDiv = document.createElement('div');
    printDiv.id = 'rolPrintArea';
    printDiv.style.setProperty('--rol-row-height',      altoFilaMm + 'mm');
    printDiv.style.setProperty('--rol-font-size',       fs + 'pt');
    printDiv.style.setProperty('--rol-font-titulo',     (fs + 5) + 'pt');
    printDiv.style.setProperty('--rol-font-subtitulo',  (fs + 2) + 'pt');
    printDiv.innerHTML = printHtml;
    document.body.appendChild(printDiv);

    // Inyectar <style> en <head> — UNICA forma confiable de forzar colores
    // sin que Chrome los ignore cuando "Graficos de fondo" esta desactivado
    const styleId = 'rolPrintColorStyle';
    let styleEl = document.getElementById(styleId);
    if (!styleEl) {
        styleEl = document.createElement('style');
        styleEl.id = styleId;
        document.head.appendChild(styleEl);
    }
    styleEl.textContent = `
        #rolPrintArea, #rolPrintArea * {
            -webkit-print-color-adjust: exact !important;
            color-adjust: exact !important;
            print-color-adjust: exact !important;
        }
        #rolPrintArea th.th-wd { background-color: #d4c5a0 !important; }
        #rolPrintArea th.th-we { background-color: #b8a878 !important; }
        #rolPrintArea td.td-we { background-color: #fdf9e3 !important; }
        #rolPrintArea td.td-empty { background-color: #f0f0f0 !important; }
        #rolPrintArea .pv-row    { height: var(--rol-row-height, 35mm) !important; }
    `;

    cerrarPreviewRol();

    setTimeout(() => {
        window.print();
        setTimeout(() => {
            const pd = document.getElementById('rolPrintArea');
            if (pd) pd.remove();
            const se = document.getElementById(styleId);
            if (se) se.remove();
        }, 1500);
    }, 200);
}
