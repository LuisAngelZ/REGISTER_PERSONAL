// ============ ESTADO GLOBAL ============
const API_URL = window.location.origin;
const API_KEY = localStorage.getItem('api_key') || '';
let personalActual = null;
let dispositivoConectado = false;
let infoDispositivo = null;
let usuarioActual = null;
let _modoRegistro = false;
let _csrfToken = '';

// ============ CONSTANTES ============
const DURACION_DIAS = { '3_meses': 85, '6_meses': 180, '1_anio': 365 };

const PUESTOS_LABEL = {
    'cajero': 'Cajero', 'mesero': 'Mesero', 'cocinero': 'Cocinero',
    'lavaplatos': 'Lavaplatos', 'servidora': 'Servidora', 'guardia': 'Guardia',
    'despacho': 'Despacho', 'otros': 'Otros'
};

const DIAS_LABEL = {
    'lunes': 'Lunes', 'martes': 'Martes', 'miercoles': 'Miercoles',
    'jueves': 'Jueves', 'viernes': 'Viernes', 'sabado': 'Sabado', 'domingo': 'Domingo'
};

const TURNOS_HORARIOS = {
    'mañana':   { entrada: '08:00', salida: '17:00' },
    'tarde':    { entrada: '13:00', salida: '22:00' },
    'especial': { entrada: '12:00', salida: '21:00' },
};

// ============ HELPERS ============
function escapeHtml(text) {
    if (text === null || text === undefined) return '';
    const div = document.createElement('div');
    div.textContent = String(text);
    return div.innerHTML;
}

async function obtenerCsrfToken() {
    try {
        const resp = await fetch(`${API_URL}/api/csrf-token`);
        const data = await resp.json();
        _csrfToken = data.csrf_token;
    } catch (e) {
        console.error('No se pudo obtener CSRF token:', e);
    }
}

function apiHeaders(extra = {}) {
    return {
        'Content-Type': 'application/json',
        'X-API-Key': API_KEY,
        'X-CSRF-Token': _csrfToken,
        ...extra
    };
}

async function apiFetch(url, options = {}) {
    if (!options.headers) options.headers = {};
    options.headers['X-API-Key'] = API_KEY;
    if (options.method && ['POST', 'PUT', 'DELETE'].includes(options.method.toUpperCase())) {
        options.headers['X-CSRF-Token'] = _csrfToken;
    }
    const resp = await fetch(url, options);
    // Session/auth expiry: si 401 en ruta protegida, redirigir a login
    if (resp.status === 401 && !url.includes('/auth/')) {
        mostrarAlerta('Sesion expirada. Redirigiendo al login...', 'error');
        setTimeout(() => cerrarSesion(), 1500);
    }
    return resp;
}

function mostrarAlerta(mensaje, tipo = 'info') {
    const container = document.getElementById('alerts');
    const alerta = document.createElement('div');
    alerta.className = `alert alert-${tipo}`;
    alerta.textContent = mensaje;
    container.appendChild(alerta);
    setTimeout(() => alerta.remove(), 4000);
}

function switchSection(sectionId, btn) {
    document.querySelectorAll('.section').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
    document.getElementById(sectionId).classList.add('active');
    btn.classList.add('active');
}

function cambiarTurno(turno, inputEntradaId, inputSalidaId) {
    const horarios = TURNOS_HORARIOS[turno];
    if (horarios) {
        document.getElementById(inputEntradaId).value = horarios.entrada;
        document.getElementById(inputSalidaId).value = horarios.salida;
    }
}

function calcularFechaFin(inputInicioId, selectDuracionId, inputFinId) {
    const inicio = document.getElementById(inputInicioId).value;
    const duracion = document.getElementById(selectDuracionId).value;
    if (!inicio || !duracion) {
        document.getElementById(inputFinId).value = '';
        return;
    }
    const dias = DURACION_DIAS[duracion] || 85;
    const fechaInicio = new Date(inicio + 'T00:00:00');
    fechaInicio.setDate(fechaInicio.getDate() + dias);
    const y = fechaInicio.getFullYear();
    const m = String(fechaInicio.getMonth() + 1).padStart(2, '0');
    const d = String(fechaInicio.getDate()).padStart(2, '0');
    document.getElementById(inputFinId).value = `${y}-${m}-${d}`;
}

// ============ MODAL DE CONFIRMACION ============
function confirmar(titulo, mensaje, onConfirm) {
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.onclick = (e) => { if (e.target === modal) modal.remove(); };
    modal.innerHTML = `
        <div class="modal-content" style="max-width:420px;">
            <div class="modal-header">
                <h2>${escapeHtml(titulo)}</h2>
                <p>${escapeHtml(mensaje)}</p>
            </div>
            <div class="modal-footer" style="display:flex;gap:10px;justify-content:flex-end;">
                <button class="btn btn-sm btn-ghost" onclick="this.closest('.modal-overlay').remove()">Cancelar</button>
                <button class="btn btn-sm btn-danger" id="_confirmBtn">Confirmar</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
    modal.querySelector('#_confirmBtn').onclick = () => {
        modal.remove();
        onConfirm();
    };
}

// ============ LOADING STATE EN BOTONES ============
function btnLoading(btn, loading) {
    if (loading) {
        btn.dataset.originalText = btn.textContent;
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner"></span> Procesando...';
    } else {
        btn.disabled = false;
        btn.textContent = btn.dataset.originalText || 'OK';
    }
}

// ============ DARK MODE ============
function toggleDarkMode() {
    const html = document.documentElement;
    const isDark = html.getAttribute('data-theme') === 'dark';
    if (isDark) {
        html.removeAttribute('data-theme');
        localStorage.removeItem('theme');
    } else {
        html.setAttribute('data-theme', 'dark');
        localStorage.setItem('theme', 'dark');
    }
}

// Restore saved theme on load
(function() {
    if (localStorage.getItem('theme') === 'dark') {
        document.documentElement.setAttribute('data-theme', 'dark');
    }
})();

document.addEventListener('change', (e) => {
    if (e.target.id === 'fechaInicio' || e.target.id === 'duracionContrato') {
        calcularFechaFin('fechaInicio', 'duracionContrato', 'fechaFin');
    }
    if (e.target.id === 'editFechaInicio' || e.target.id === 'editDuracionContrato') {
        calcularFechaFin('editFechaInicio', 'editDuracionContrato', 'editFechaFin');
    }
});
