// ============ REPORTE ASISTENCIA ============
let _reporteData = null;
const DIAS_LABEL_CORTO = {lunes:'Lun',martes:'Mar',miercoles:'Mie',jueves:'Jue',viernes:'Vie',sabado:'Sab',domingo:'Dom'};

async function cargarReporteInit() {
    const select  = document.getElementById('reportePersonal');
    const mesEl   = document.getElementById('reporteMes');
    const anioEl  = document.getElementById('reporteAnio');
    if (!select || !mesEl || !anioEl) return;
    try {
        const resp = await apiFetch(`${API_URL}/api/personal/?activos=true&limit=200`);
        if (resp.ok) {
            const personal = await resp.json();
            select.innerHTML = '<option value="">-- Seleccionar --</option>';
            personal.forEach(p => {
                select.innerHTML += `<option value="${escapeHtml(p.id)}">${escapeHtml(p.nombre)} ${escapeHtml(p.apellido)} - ${escapeHtml(p.turno || '')}</option>`;
            });
        }
    } catch(e) { console.error(e); }

    const now = new Date();
    mesEl.value  = now.getMonth();
    anioEl.value = now.getFullYear();
}

async function cargarReporte() {
    const personalId = document.getElementById('reportePersonal').value;
    if (!personalId) return;

    const mes = parseInt(document.getElementById('reporteMes').value) + 1;
    const anio = parseInt(document.getElementById('reporteAnio').value);

    try {
        const [repResp, perResp] = await Promise.all([
            apiFetch(`${API_URL}/api/personal/${personalId}/reporte-mensual?mes=${mes}&anio=${anio}`),
            apiFetch(`${API_URL}/api/personal/${personalId}`),
        ]);
        if (!repResp.ok) throw new Error('Error al cargar reporte');
        _reporteData = await repResp.json();
        // Pre-llenar sueldo desde la BD si existe
        if (perResp.ok) {
            const per = await perResp.json();
            if (per.sueldo) {
                document.getElementById('reporteSueldo').value = parseFloat(per.sueldo);
            }
        }
        renderReporte();
    } catch(e) {
        mostrarAlerta(e.message, 'error');
    }
}

function renderReporte() {
    if (!_reporteData) return;
    const data = _reporteData;
    const tbody = document.getElementById('reporteBody');

    let html = '';
    data.dias.forEach(dia => {
        const fechaParts = dia.fecha.split('-');
        const fechaDisplay = `${fechaParts[2]}/${fechaParts[1]}/${fechaParts[0]}`;
        const diaLabel = DIAS_LABEL_CORTO[dia.dia_semana] || dia.dia_semana;

        let rowClass = '';
        if (dia.es_libre) rowClass = 'dia-libre';
        else if (!dia.trabajo && new Date(dia.fecha) <= new Date()) rowClass = 'dia-falta';

        const ingreso = dia.hora_ingreso || '';
        const salida = dia.hora_salida || '';
        const retraso = dia.minutos_retraso > 0 ? `<span class="retraso-val">${dia.minutos_retraso}</span>` : '0';
        const extra = dia.minutos_extra > 0 ? `<span class="extra-val">${dia.minutos_extra}</span>` : '0';

        html += `<tr class="${rowClass}" data-fecha="${dia.fecha}">
            <td>${fechaDisplay}</td>
            <td>${diaLabel}</td>
            <td class="cell-editable" onclick="editarCelda(this, '${dia.fecha}', 'ingreso', '${ingreso}')">${ingreso || '<span style="color:var(--slate-300);">--:--</span>'}</td>
            <td class="cell-editable" onclick="editarCelda(this, '${dia.fecha}', 'salida', '${salida}')">${salida || '<span style="color:var(--slate-300);">--:--</span>'}</td>
            <td>${dia.es_libre ? '' : retraso}</td>
            <td>${dia.es_libre ? '' : extra}</td>
            <td>${dia.es_libre ? '<span style="font-size:0.7rem;color:var(--accent);">LIBRE</span>' : ''}</td>
        </tr>`;
    });

    tbody.innerHTML = html;

    const diasDescanso = data.dias.filter(d => d.es_libre).length;
    document.getElementById('repDiasTrab').textContent = data.dias_trabajados;
    document.getElementById('repDiasDescanso').textContent = diasDescanso;
    document.getElementById('repDiasFalta').textContent = data.dias_falta;
    document.getElementById('repTotalDias').textContent = data.dias_en_mes;
    document.getElementById('repMinRetraso').textContent = data.total_minutos_retraso;
    document.getElementById('repMinExtra').textContent = data.total_minutos_extra;

    recalcularSalario();
}

async function guardarSueldo() {
    if (!_reporteData) return;
    const personalId = document.getElementById('reportePersonal').value;
    if (!personalId) return;
    const sueldo = parseFloat(document.getElementById('reporteSueldo').value) || null;
    try {
        await apiFetch(`${API_URL}/api/personal/${personalId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sueldo }),
        });
    } catch(e) { /* silencioso */ }
}

function recalcularSalario() {
    if (!_reporteData) return;
    const sueldo = parseFloat(document.getElementById('reporteSueldo').value) || 0;
    const data = _reporteData;

    const diasLaborales = data.dias_en_mes - data.dias.filter(d => d.es_libre).length;
    const horasTurno = calcularHorasTurno(data.hora_entrada, data.hora_salida);
    const sueldoPorMinuto = diasLaborales > 0 ? sueldo / (diasLaborales * horasTurno * 60) : 0;

    const descRetraso = Math.round(data.total_minutos_retraso * sueldoPorMinuto * 100) / 100;
    const pagoExtra = Math.round(data.total_minutos_extra * sueldoPorMinuto * 100) / 100;
    const descFaltas = diasLaborales > 0 ? Math.round(data.dias_falta * (sueldo / diasLaborales) * 100) / 100 : 0;
    const total = Math.round((sueldo - descRetraso - descFaltas + pagoExtra) * 100) / 100;

    document.getElementById('repSueldo').textContent = sueldo.toFixed(2) + ' Bs';
    document.getElementById('repDescRetraso').textContent = '-' + descRetraso.toFixed(2) + ' Bs';
    document.getElementById('repPagoExtra').textContent = '+' + pagoExtra.toFixed(2) + ' Bs';
    document.getElementById('repTotal').textContent = total.toFixed(2) + ' Bs';
}

function calcularHorasTurno(entrada, salida) {
    try {
        const [h1, m1] = entrada.split(':').map(Number);
        const [h2, m2] = salida.split(':').map(Number);
        return ((h2 * 60 + m2) - (h1 * 60 + m1)) / 60;
    } catch(e) { return 9; }
}

function editarCelda(td, fecha, tipo, valorActual) {
    if (td.querySelector('input')) return;

    const input = document.createElement('input');
    input.type = 'time';
    input.value = valorActual;
    input.style.width = '90px';

    td.innerHTML = '';
    td.appendChild(input);
    input.focus();

    const guardar = async () => {
        const nuevoValor = input.value;
        const personalId = document.getElementById('reportePersonal').value;

        const row = td.closest('tr');
        const cells = row.querySelectorAll('.cell-editable');
        let hora_ingreso, hora_salida;

        if (tipo === 'ingreso') {
            hora_ingreso = nuevoValor || null;
            const salidaCell = cells[1];
            const salidaText = salidaCell.textContent.trim();
            hora_salida = (salidaText && salidaText !== '--:--') ? salidaText : null;
        } else {
            hora_salida = nuevoValor || null;
            const ingresoCell = cells[0];
            const ingresoText = ingresoCell.textContent.trim();
            hora_ingreso = (ingresoText && ingresoText !== '--:--') ? ingresoText : null;
        }

        try {
            const resp = await apiFetch(`${API_URL}/api/personal/asistencia-manual`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    personal_id: parseInt(personalId),
                    fecha: fecha,
                    hora_ingreso: hora_ingreso,
                    hora_salida: hora_salida,
                })
            });
            if (resp.ok) {
                mostrarAlerta('Asistencia actualizada', 'success');
                cargarReporte();
            } else {
                mostrarAlerta('Error al guardar', 'error');
                td.textContent = valorActual || '--:--';
            }
        } catch(e) {
            mostrarAlerta('Error de conexion', 'error');
            td.textContent = valorActual || '--:--';
        }
    };

    input.addEventListener('blur', guardar);
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') input.blur();
        if (e.key === 'Escape') {
            td.textContent = valorActual || '--:--';
        }
    });
}

// ============ EXPORTAR REPORTE ============
async function exportarReporte(formato) {
    const personalId = document.getElementById('reportePersonal').value;
    if (!personalId) {
        mostrarAlerta('Selecciona un personal primero', 'error');
        return;
    }
    const mes = parseInt(document.getElementById('reporteMes').value) + 1;
    const anio = parseInt(document.getElementById('reporteAnio').value);
    const url = `${API_URL}/api/personal/${personalId}/exportar-reporte?mes=${mes}&anio=${anio}&formato=${formato}`;

    try {
        const resp = await apiFetch(url);
        if (!resp.ok) throw new Error('Error al exportar');
        const blob = await resp.blob();
        const ext = formato === 'excel' ? 'xlsx' : 'csv';
        const filename = resp.headers.get('Content-Disposition')?.match(/filename=(.+)/)?.[1] || `reporte.${ext}`;
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = filename;
        a.click();
        URL.revokeObjectURL(a.href);
    } catch (e) {
        mostrarAlerta('Error al exportar: ' + e.message, 'error');
    }
}
