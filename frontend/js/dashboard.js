// ============ DASHBOARD ============
let _chartPuestos = null;
let _chartRetrasos = null;
let _chartFaltas = null;

const PUESTOS_COLORES = {
    'cajero':'#3b82f6','mesero':'#10b981','cocinero':'#f59e0b','lavaplatos':'#6366f1',
    'servidora':'#ec4899','guardia':'#14b8a6','despacho':'#8b5cf6','otros':'#64748b'
};

async function cargarDashboard() {
    const mesEl  = document.getElementById('dashMes');
    const anioEl = document.getElementById('dashAnio');
    if (!mesEl || !anioEl) return;
    const mes  = parseInt(mesEl.value) + 1;
    const anio = parseInt(anioEl.value);

    try {
        const resp = await apiFetch(`${API_URL}/api/personal/stats/dashboard?mes=${mes}&anio=${anio}`);
        if (!resp.ok) throw new Error('Error al cargar dashboard');
        const data = await resp.json();

        document.getElementById('dashTotal').textContent = data.total_personal;
        document.getElementById('dashFaltas').textContent = data.total_dias_falta;
        document.getElementById('dashRetrasos').textContent = data.total_minutos_retraso;
        document.getElementById('dashExtras').textContent = data.total_minutos_extra;

        renderChartPuestos(data.por_puesto, data.total_personal);
        renderChartRetrasos(data.top_retrasos);
        renderChartFaltas(data.top_faltas);

    } catch (error) {
        console.error('Error dashboard:', error);
    }
}

function renderChartPuestos(porPuesto, total) {
    const labels = [];
    const valores = [];
    const colores = [];

    for (const [puesto, count] of Object.entries(porPuesto)) {
        labels.push(PUESTOS_LABEL[puesto] || puesto);
        valores.push(count);
        colores.push(PUESTOS_COLORES[puesto] || '#64748b');
    }

    if (_chartPuestos) _chartPuestos.destroy();

    const ctx = document.getElementById('chartPuestos');
    if (!ctx) return;

    _chartPuestos = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: valores,
                backgroundColor: colores,
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { font: { size: 11 }, padding: 12 }
                }
            }
        }
    });
}

function renderChartRetrasos(topRetrasos) {
    const filtered = (topRetrasos || []).filter(r => r.minutos_retraso > 0);
    const canvas = document.getElementById('chartRetrasos');
    const emptyMsg = document.getElementById('dashTopRetrasosEmpty');

    if (!filtered.length) {
        if (canvas) canvas.style.display = 'none';
        if (emptyMsg) emptyMsg.style.display = 'block';
        if (_chartRetrasos) { _chartRetrasos.destroy(); _chartRetrasos = null; }
        return;
    }

    if (canvas) canvas.style.display = 'block';
    if (emptyMsg) emptyMsg.style.display = 'none';
    if (_chartRetrasos) _chartRetrasos.destroy();

    _chartRetrasos = new Chart(canvas, {
        type: 'bar',
        data: {
            labels: filtered.map(r => r.nombre.split(' ').slice(0, 2).join(' ')),
            datasets: [{
                label: 'Min. Retraso',
                data: filtered.map(r => r.minutos_retraso),
                backgroundColor: '#ef4444cc',
                borderColor: '#ef4444',
                borderWidth: 1,
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            plugins: { legend: { display: false } },
            scales: {
                x: { beginAtZero: true, grid: { display: false } },
                y: { grid: { display: false }, ticks: { font: { size: 11 } } }
            }
        }
    });
}

function renderChartFaltas(topFaltas) {
    const filtered = (topFaltas || []).filter(f => f.dias_falta > 0);
    const canvas = document.getElementById('chartFaltas');
    const emptyMsg = document.getElementById('dashTopFaltasEmpty');

    if (!filtered.length) {
        if (canvas) canvas.style.display = 'none';
        if (emptyMsg) emptyMsg.style.display = 'block';
        if (_chartFaltas) { _chartFaltas.destroy(); _chartFaltas = null; }
        return;
    }

    if (canvas) canvas.style.display = 'block';
    if (emptyMsg) emptyMsg.style.display = 'none';
    if (_chartFaltas) _chartFaltas.destroy();

    _chartFaltas = new Chart(canvas, {
        type: 'bar',
        data: {
            labels: filtered.map(f => f.nombre.split(' ').slice(0, 2).join(' ')),
            datasets: [{
                label: 'Dias Falta',
                data: filtered.map(f => f.dias_falta),
                backgroundColor: '#f59e0bcc',
                borderColor: '#f59e0b',
                borderWidth: 1,
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            plugins: { legend: { display: false } },
            scales: {
                x: { beginAtZero: true, grid: { display: false } },
                y: { grid: { display: false }, ticks: { font: { size: 11 } } }
            }
        }
    });
}

// Set dashboard month to current
(function() {
    const now = new Date();
    const dashMes = document.getElementById('dashMes');
    const dashAnio = document.getElementById('dashAnio');
    if (dashMes) dashMes.value = now.getMonth();
    if (dashAnio) dashAnio.value = now.getFullYear();
})();
