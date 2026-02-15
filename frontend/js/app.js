const API_URL = window.location.origin;
let personalActual = null;
let dispositivoConectado = false;
let infoDispositivo = null;

// ============ INIT ============
window.addEventListener('load', async () => {
    await cargarConfigEnLogin();
});

async function cargarConfigEnLogin() {
    try {
        const response = await fetch(`${API_URL}/api/zkteco/config`);
        if (response.ok) {
            const config = await response.json();
            document.getElementById('loginIp').value = config.ip || '';
            document.getElementById('loginPuerto').value = config.puerto || 4370;
            document.getElementById('loginPassword').value = config.password || 0;
            if (config.guardado && config.ip) {
                intentarConexion();
            }
        }
    } catch (error) {
        console.error('Error cargando config:', error);
    }
}

// ============ LOGIN ============
async function intentarConexion() {
    const ip = document.getElementById('loginIp').value.trim();
    const puerto = parseInt(document.getElementById('loginPuerto').value) || 4370;
    const password = parseInt(document.getElementById('loginPassword').value) || 0;
    const statusDiv = document.getElementById('loginStatus');
    const btn = document.getElementById('btnConectar');

    if (!ip) {
        statusDiv.className = 'login-status error';
        statusDiv.textContent = 'Ingresa la IP del dispositivo';
        return;
    }

    btn.disabled = true;
    btn.textContent = 'Conectando...';
    statusDiv.className = 'login-status conectando';
    statusDiv.innerHTML = '<span class="spinner"></span> Conectando al dispositivo...';

    try {
        await fetch(`${API_URL}/api/zkteco/configurar-ip`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ip, puerto, password })
        });

        const response = await fetch(`${API_URL}/api/zkteco/test-conexion`);
        const data = await response.json();

        if (response.ok) {
            dispositivoConectado = true;
            infoDispositivo = data.info;
            statusDiv.className = 'login-status success';
            statusDiv.textContent = 'Conexion exitosa!';
            setTimeout(() => entrarAlSistema(), 600);
        } else {
            statusDiv.className = 'login-status error';
            statusDiv.textContent = (data.detail || 'Verifica la IP y que el dispositivo este encendido');
            btn.disabled = false;
            btn.textContent = 'Conectar';
        }
    } catch (error) {
        statusDiv.className = 'login-status error';
        statusDiv.textContent = 'Error: Verifica que el servidor backend este corriendo';
        btn.disabled = false;
        btn.textContent = 'Conectar';
    }
}

function entrarAlSistema() {
    document.getElementById('loginScreen').style.display = 'none';
    document.getElementById('mainApp').classList.add('visible');
    cargarConfigGuardada();
    cargarPersonal();
    cargarEstadisticas();
    actualizarDevicePill();
}

function entrarSinDispositivo() {
    dispositivoConectado = false;
    infoDispositivo = null;
    document.getElementById('loginScreen').style.display = 'none';
    document.getElementById('mainApp').classList.add('visible');
    actualizarDevicePill();
    cargarConfigGuardada();
    cargarPersonal();
    cargarEstadisticas();
}

// ============ DEVICE PILL ============
function actualizarDevicePill() {
    const pill = document.getElementById('devicePill');
    const text = document.getElementById('devicePillText');
    const dot = pill.querySelector('.pill-dot');

    if (dispositivoConectado && infoDispositivo) {
        pill.className = 'device-pill online';
        dot.className = 'pill-dot green';
        text.textContent = `${infoDispositivo.nombre_dispositivo || 'ZKTeco'} | ${infoDispositivo.usuarios_registrados || 0} usuarios`;
    } else {
        pill.className = 'device-pill offline';
        dot.className = 'pill-dot red';
        text.textContent = 'Sin dispositivo';
    }
}

async function refrescarEstadoDispositivo() {
    try {
        const response = await fetch(`${API_URL}/api/zkteco/test-conexion`);
        const data = await response.json();
        if (response.ok) {
            dispositivoConectado = true;
            infoDispositivo = data.info;
        } else {
            dispositivoConectado = false;
            infoDispositivo = null;
        }
    } catch {
        dispositivoConectado = false;
        infoDispositivo = null;
    }
    actualizarDevicePill();
}

// ============ CONFIG ============
async function cargarConfigGuardada() {
    try {
        const response = await fetch(`${API_URL}/api/zkteco/config`);
        if (response.ok) {
            const config = await response.json();
            document.getElementById('ipZkteco').value = config.ip || '';
            document.getElementById('puertoZkteco').value = config.puerto || 4370;
            document.getElementById('passwordZkteco').value = config.password || 0;
            if (config.guardado) {
                document.getElementById('configInfo').innerHTML =
                    `<strong>Dispositivo configurado</strong> &mdash; ${config.ip}:${config.puerto}`;
            }
        }
    } catch (error) {
        console.error('Error cargando config:', error);
    }
}

// ============ CALCULAR FECHA FIN ============
const DURACION_DIAS = {
    '3_meses': 85,
    '6_meses': 180,
    '1_anio': 365,
};

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

// Auto-calc on date change
document.addEventListener('change', (e) => {
    if (e.target.id === 'fechaInicio' || e.target.id === 'duracionContrato') {
        calcularFechaFin('fechaInicio', 'duracionContrato', 'fechaFin');
    }
    if (e.target.id === 'editFechaInicio' || e.target.id === 'editDuracionContrato') {
        calcularFechaFin('editFechaInicio', 'editDuracionContrato', 'editFechaFin');
    }
});

const PUESTOS_LABEL = {
    'cajero': 'Cajero', 'mesero': 'Mesero', 'cocinero': 'Cocinero',
    'lavaplatos': 'Lavaplatos', 'servidora': 'Servidora', 'guardia': 'Guardia',
    'despacho': 'Despacho', 'otros': 'Otros'
};

const DIAS_LABEL = {
    'lunes': 'Lunes', 'martes': 'Martes', 'miercoles': 'Miercoles',
    'jueves': 'Jueves', 'viernes': 'Viernes', 'sabado': 'Sabado', 'domingo': 'Domingo'
};

// ============ TURNOS ============
const TURNOS_HORARIOS = {
    'mañana':   { entrada: '08:00', salida: '17:00' },
    'tarde':    { entrada: '13:00', salida: '22:00' },
    'especial': { entrada: '12:00', salida: '21:00' },
};

function cambiarTurno(turno, inputEntradaId, inputSalidaId) {
    const horarios = TURNOS_HORARIOS[turno];
    if (horarios) {
        document.getElementById(inputEntradaId).value = horarios.entrada;
        document.getElementById(inputSalidaId).value = horarios.salida;
    }
}

// ============ ALERTS ============
function mostrarAlerta(mensaje, tipo = 'info') {
    const container = document.getElementById('alerts');
    const alerta = document.createElement('div');
    alerta.className = `alert alert-${tipo}`;
    alerta.textContent = mensaje;
    container.appendChild(alerta);
    setTimeout(() => alerta.remove(), 4000);
}

// ============ NAVIGATION ============
function switchSection(sectionId, btn) {
    document.querySelectorAll('.section').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
    document.getElementById(sectionId).classList.add('active');
    btn.classList.add('active');
}

// ============ CREAR PERSONAL ============
async function crearPersonal(event) {
    event.preventDefault();

    const datos = {
        nombre: document.getElementById('nombre').value,
        apellido: document.getElementById('apellido').value,
        documento: document.getElementById('documento').value,
        puesto: document.getElementById('puesto').value,
        turno: document.getElementById('turno').value,
        hora_entrada: document.getElementById('horaEntrada').value,
        hora_salida: document.getElementById('horaSalida').value,
        fecha_inicio: document.getElementById('fechaInicio').value || null,
        duracion_contrato: document.getElementById('duracionContrato').value,
    };

    try {
        const response = await fetch(`${API_URL}/api/personal/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(datos)
        });

        if (!response.ok) throw new Error('Error al crear personal');

        const nuevoPersonal = await response.json();
        mostrarAlerta('Personal creado exitosamente', 'success');
        document.getElementById('formCrear').reset();
        cargarPersonal();
        cargarEstadisticas();

        if (dispositivoConectado && nuevoPersonal.id) {
            try {
                const expRes = await fetch(`${API_URL}/api/zkteco/exportar-usuario`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ personal_id: nuevoPersonal.id })
                });
                const expData = await expRes.json();
                if (expRes.ok) {
                    mostrarAlerta(`Exportado al dispositivo: ${expData.nombre} (UID: ${expData.uid})`, 'success');
                    cargarPersonal();
                } else {
                    mostrarAlerta('Creado en BD pero no se pudo exportar al dispositivo', 'error');
                }
            } catch (expErr) {
                mostrarAlerta('Creado en BD pero fallo la exportacion', 'error');
            }
        }
    } catch (error) {
        mostrarAlerta('Error: ' + error.message, 'error');
    }
}

// ============ BUSCAR PERSONAL ============
async function buscarPersonal() {
    const id = document.getElementById('buscarId').value;
    if (!id) {
        mostrarAlerta('Ingresa un ID', 'error');
        return;
    }

    try {
        const response = await fetch(`${API_URL}/api/personal/${id}`);
        if (!response.ok) throw new Error('Personal no encontrado');

        const personal = await response.json();
        personalActual = personal;

        document.getElementById('editNombre').value = personal.nombre;
        document.getElementById('editApellido').value = personal.apellido;
        document.getElementById('editPuesto').value = personal.puesto || 'otros';
        document.getElementById('editTurno').value = personal.turno || 'mañana';
        const diaLabel = DIAS_LABEL[personal.dia_libre] || personal.dia_libre || 'Sin asignar';
        document.getElementById('editDiaLibre').value = diaLabel;
        document.getElementById('editHoraEntrada').value = personal.hora_entrada || '08:00';
        document.getElementById('editHoraSalida').value = personal.hora_salida || '17:00';
        document.getElementById('editFechaInicio').value = personal.fecha_inicio || '';
        document.getElementById('editDuracionContrato').value = personal.duracion_contrato || '3_meses';
        document.getElementById('editFechaFin').value = personal.fecha_fin || '';
        if (personal.fecha_inicio) {
            calcularFechaFin('editFechaInicio', 'editDuracionContrato', 'editFechaFin');
        }

        document.getElementById('formEditar').style.display = 'block';
        mostrarAlerta('Personal encontrado: ' + personal.nombre + ' ' + personal.apellido, 'success');
    } catch (error) {
        mostrarAlerta(error.message, 'error');
    }
}

// ============ ACTUALIZAR PERSONAL ============
async function actualizarPersonal(event) {
    event.preventDefault();
    if (!personalActual) return;

    const datos = {
        nombre: document.getElementById('editNombre').value,
        apellido: document.getElementById('editApellido').value,
        puesto: document.getElementById('editPuesto').value,
        turno: document.getElementById('editTurno').value,
        hora_entrada: document.getElementById('editHoraEntrada').value,
        hora_salida: document.getElementById('editHoraSalida').value,
        fecha_inicio: document.getElementById('editFechaInicio').value || null,
        duracion_contrato: document.getElementById('editDuracionContrato').value,
    };

    try {
        const response = await fetch(`${API_URL}/api/personal/${personalActual.id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(datos)
        });

        if (!response.ok) throw new Error('Error al actualizar');
        mostrarAlerta('Personal actualizado', 'success');

        if (dispositivoConectado && personalActual.id) {
            try {
                const expRes = await fetch(`${API_URL}/api/zkteco/exportar-usuario`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ personal_id: personalActual.id })
                });
                const expData = await expRes.json();
                if (expRes.ok) {
                    mostrarAlerta(`Actualizado en dispositivo: ${expData.nombre}`, 'success');
                } else {
                    mostrarAlerta('Actualizado en BD pero fallo exportar al dispositivo', 'error');
                }
            } catch (expErr) {
                mostrarAlerta('Actualizado en BD pero fallo la exportacion', 'error');
            }
        }

        cancelarEdicion();
        cargarPersonal();
    } catch (error) {
        mostrarAlerta('Error: ' + error.message, 'error');
    }
}

function cancelarEdicion() {
    document.getElementById('formEditar').style.display = 'none';
    document.getElementById('buscarId').value = '';
    personalActual = null;
}

// ============ CARGAR PERSONAL (CARDS) ============
async function cargarPersonal() {
    try {
        const response = await fetch(`${API_URL}/api/personal/`);
        if (!response.ok) throw new Error('Error al cargar personal');

        const personal = await response.json();
        const container = document.getElementById('personnelContainer');

        if (personal.length === 0) {
            container.innerHTML = `
                <div class="empty-state" style="grid-column:1/-1;">
                    <div class="empty-icon">&#128100;</div>
                    <p>No hay personal registrado</p>
                </div>
            `;
            return;
        }

        // Filter by CI or full name
        const filtro = (document.getElementById('filtroNombre').value || '').toLowerCase();
        const filtered = filtro
            ? personal.filter(p =>
                `${p.nombre} ${p.apellido}`.toLowerCase().includes(filtro) ||
                (p.documento || '').toLowerCase().includes(filtro)
            )
            : personal;

        if (filtered.length === 0) {
            container.innerHTML = `
                <div class="empty-state" style="grid-column:1/-1;">
                    <div class="empty-icon">&#128269;</div>
                    <p>No se encontraron resultados</p>
                </div>
            `;
            return;
        }

        const DURACION_LABEL = {'3_meses':'3 Meses','6_meses':'6 Meses','1_anio':'1 Ano'};

        container.innerHTML = filtered.map(p => {
            const initials = (p.nombre[0] || '') + (p.apellido[0] || '');
            const statusClass = p.activo ? 'active' : 'inactive';
            const statusText = p.activo ? 'Activo' : 'Inactivo';
            const turnoLabel = {'mañana':'Manana','tarde':'Tarde','especial':'Especial'}[p.turno] || p.turno || '-';
            const puestoLabel = PUESTOS_LABEL[p.puesto] || p.puesto || '-';
            const diaLibreLabel = DIAS_LABEL[p.dia_libre] || p.dia_libre || '-';
            const duracionLabel = DURACION_LABEL[p.duracion_contrato] || '-';
            const fechaFinStr = p.fecha_fin ? new Date(p.fecha_fin + 'T00:00:00').toLocaleDateString('es-ES') : '-';
            const fechaInicioStr = p.fecha_inicio ? new Date(p.fecha_inicio + 'T00:00:00').toLocaleDateString('es-ES') : '-';

            return `
                <div class="person-card">
                    <div class="person-top">
                        <div class="person-avatar">${initials.toUpperCase()}</div>
                        <span class="person-status ${statusClass}">${statusText}</span>
                    </div>
                    <div class="person-name">${p.nombre} ${p.apellido}</div>
                    <div class="person-meta">
                        <span>&#128179; CI: ${p.documento}</span>
                        <span>&#128188; ${puestoLabel}</span>
                        <span>&#128197; ${fechaInicioStr} - ${fechaFinStr}</span>
                        <span>&#127774; Libre: ${diaLibreLabel}</span>
                    </div>
                    <div class="person-tags">
                        <span class="tag">${turnoLabel}</span>
                        <span class="tag">${duracionLabel}</span>
                        ${p.user_id ? `<span class="tag uid">ID: ${p.user_id}</span>` : ''}
                    </div>
                    <div class="person-actions">
                        <button class="btn btn-sm btn-success" onclick="editarPersonal(${p.id})">Editar</button>
                        <button class="btn btn-sm btn-info" onclick="verAsistencia(${p.id})">Asistencia</button>
                        <button class="btn btn-sm btn-danger" onclick="eliminarPersonal(${p.id})">Eliminar</button>
                    </div>
                </div>
            `;
        }).join('');

    } catch (error) {
        mostrarAlerta(error.message, 'error');
    }
}

function editarPersonal(id) {
    document.getElementById('buscarId').value = id;
    buscarPersonal();
    // Switch to editar section
    document.querySelectorAll('.section').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
    document.getElementById('editar-section').classList.add('active');
    document.querySelectorAll('.nav-item')[2].classList.add('active');
}

// ============ ELIMINAR ============
async function eliminarPersonal(id) {
    if (!confirm('Desactivar este personal?')) return;

    try {
        const response = await fetch(`${API_URL}/api/personal/${id}`, { method: 'DELETE' });
        if (!response.ok) throw new Error('Error al eliminar');
        mostrarAlerta('Personal desactivado', 'success');
        cargarPersonal();
        cargarEstadisticas();
    } catch (error) {
        mostrarAlerta(error.message, 'error');
    }
}

// ============ ESTADISTICAS ============
async function cargarEstadisticas() {
    try {
        const response = await fetch(`${API_URL}/api/personal/stats/total`);
        if (!response.ok) throw new Error('Error');
        const stats = await response.json();
        document.getElementById('totalPersonal').textContent = stats.total;
        document.getElementById('activosPersonal').textContent = stats.activos;
        document.getElementById('inactivosPersonal').textContent = stats.inactivos;
    } catch (error) {
        console.error(error);
    }
}

// ============ CONFIGURAR IP ============
async function configurarIP() {
    const ip = document.getElementById('ipZkteco').value;
    const puerto = parseInt(document.getElementById('puertoZkteco').value);
    const password = parseInt(document.getElementById('passwordZkteco').value) || 0;
    const statusDiv = document.getElementById('conexionStatus');

    if (!ip) {
        statusDiv.innerHTML = '<div class="alert alert-error" style="margin-top:12px;">Ingresa la IP del dispositivo</div>';
        return;
    }

    try {
        const response = await fetch(`${API_URL}/api/zkteco/configurar-ip`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ip, puerto, password })
        });
        const data = await response.json();
        if (response.ok) {
            statusDiv.innerHTML = `<div class="alert alert-success" style="margin-top:12px;">Configuracion guardada: ${ip}:${puerto}</div>`;
            document.getElementById('configInfo').innerHTML =
                `<strong>Dispositivo configurado</strong> &mdash; ${ip}:${puerto}`;
        } else {
            statusDiv.innerHTML = `<div class="alert alert-error" style="margin-top:12px;">${data.detail || 'Error'}</div>`;
        }
    } catch (error) {
        statusDiv.innerHTML = `<div class="alert alert-error" style="margin-top:12px;">${error.message}</div>`;
    }
}

// ============ TEST CONEXION ============
async function testConexion() {
    await configurarIP();
    const statusDiv = document.getElementById('conexionStatus');
    statusDiv.innerHTML = '<div style="margin-top:12px;color:var(--slate-500);font-size:0.85rem;"><span class="spinner"></span> Probando conexion...</div>';

    try {
        const response = await fetch(`${API_URL}/api/zkteco/test-conexion`);
        const data = await response.json();

        if (response.ok) {
            const info = data.info;
            statusDiv.innerHTML = `
                <div class="alert alert-success" style="margin-top:12px;">
                    <strong>Conexion exitosa</strong><br>
                    Dispositivo: ${info.nombre_dispositivo || 'ZKTeco'}<br>
                    Serial: ${info.serial_number || '-'} | MAC: ${info.mac || '-'}<br>
                    Usuarios: ${info.usuarios_registrados || 0} / ${info.capacidad_usuarios || '-'}<br>
                    Huellas: ${info.huellas_registradas || 0} / ${info.capacidad_huellas || '-'}<br>
                    Registros: ${info.registros_asistencia || 0}
                </div>
            `;
            refrescarEstadoDispositivo();
        } else {
            statusDiv.innerHTML = `<div class="alert alert-error" style="margin-top:12px;">${data.detail || 'Error de conexion'}</div>`;
        }
    } catch (error) {
        statusDiv.innerHTML = `<div class="alert alert-error" style="margin-top:12px;">${error.message}</div>`;
    }
}

// ============ SINCRONIZAR USUARIOS ============
async function sincronizarUsuarios() {
    const statusDiv = document.getElementById('syncStatus');
    statusDiv.innerHTML = '<div style="margin-top:12px;color:var(--slate-500);font-size:0.85rem;"><span class="spinner"></span> Importando usuarios...</div>';

    try {
        const response = await fetch(`${API_URL}/api/zkteco/sincronizar-usuarios`, { method: 'POST' });
        const data = await response.json();

        if (response.ok) {
            statusDiv.innerHTML = `
                <div class="alert alert-success" style="margin-top:12px;">
                    <strong>Usuarios importados</strong><br>
                    Nuevos: ${data.total_sincronizados} | Actualizados: ${data.total_actualizados || 0}<br>
                    Total en dispositivo: ${data.total_en_dispositivo}
                </div>
            `;
            cargarPersonal();
            cargarEstadisticas();
        } else {
            statusDiv.innerHTML = `<div class="alert alert-error" style="margin-top:12px;">${data.detail || 'Error'}</div>`;
        }
    } catch (error) {
        statusDiv.innerHTML = `<div class="alert alert-error" style="margin-top:12px;">${error.message}</div>`;
    }
}

// ============ VER ASISTENCIA ============
async function verAsistencia(personalId) {
    try {
        if (dispositivoConectado) {
            mostrarAlerta('Sincronizando asistencia...', 'info');
            try {
                await fetch(`${API_URL}/api/zkteco/sincronizar-registros`, { method: 'POST' });
            } catch (syncErr) {
                console.warn('Sync error:', syncErr);
            }
        }

        const response = await fetch(`${API_URL}/api/personal/${personalId}/asistencia?limit=500`);
        if (!response.ok) throw new Error('Error al cargar asistencia');
        const data = await response.json();

        let bodyHtml = '';

        if (data.registros.length === 0) {
            bodyHtml = `
                <div class="empty-state">
                    <div class="empty-icon">&#128203;</div>
                    <p>No hay registros de asistencia</p>
                </div>
            `;
        } else {
            bodyHtml = '<table class="att-table"><thead><tr><th>Fecha</th><th>Hora</th><th>Tipo</th></tr></thead><tbody>';
            data.registros.forEach(reg => {
                const fecha = new Date(reg.fecha_hora);
                const fechaStr = fecha.toLocaleDateString('es-ES');
                const horaStr = fecha.toLocaleTimeString('es-ES', {hour:'2-digit', minute:'2-digit', second:'2-digit'});
                const esEntrada = reg.tipo === 'entrada';
                const badge = esEntrada
                    ? '<span class="badge-entrada">Entrada</span>'
                    : '<span class="badge-salida">Salida</span>';
                bodyHtml += `<tr><td>${fechaStr}</td><td>${horaStr}</td><td>${badge}</td></tr>`;
            });
            bodyHtml += '</tbody></table>';
        }

        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.onclick = (e) => { if (e.target === modal) modal.remove(); };
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h2>${data.nombre}</h2>
                    <p>${data.total_registros} registros de asistencia</p>
                </div>
                <div class="modal-body">
                    ${bodyHtml}
                </div>
                <div class="modal-footer">
                    <button class="btn btn-ghost" onclick="this.closest('.modal-overlay').remove()">Cerrar</button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
    } catch (error) {
        mostrarAlerta(error.message, 'error');
    }
}
// ============ REPORTE ASISTENCIA ============
let _reporteData = null;
const DIAS_LABEL_CORTO = {lunes:'Lun',martes:'Mar',miercoles:'Mie',jueves:'Jue',viernes:'Vie',sabado:'Sab',domingo:'Dom'};

async function cargarReporteInit() {
    // Populate personnel dropdown
    const select = document.getElementById('reportePersonal');
    try {
        const resp = await fetch(`${API_URL}/api/personal/?activos=true&limit=200`);
        if (resp.ok) {
            const personal = await resp.json();
            select.innerHTML = '<option value="">-- Seleccionar --</option>';
            personal.forEach(p => {
                select.innerHTML += `<option value="${p.id}">${p.nombre} ${p.apellido} - ${p.turno || ''}</option>`;
            });
        }
    } catch(e) { console.error(e); }

    // Set current month/year
    const now = new Date();
    document.getElementById('reporteMes').value = now.getMonth();
    document.getElementById('reporteAnio').value = now.getFullYear();
}

async function cargarReporte() {
    const personalId = document.getElementById('reportePersonal').value;
    if (!personalId) return;

    const mes = parseInt(document.getElementById('reporteMes').value) + 1; // API uses 1-12
    const anio = parseInt(document.getElementById('reporteAnio').value);

    try {
        const resp = await fetch(`${API_URL}/api/personal/${personalId}/reporte-mensual?mes=${mes}&anio=${anio}`);
        if (!resp.ok) throw new Error('Error al cargar reporte');
        _reporteData = await resp.json();
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

    // Update summary
    const diasDescanso = data.dias.filter(d => d.es_libre).length;
    document.getElementById('repDiasTrab').textContent = data.dias_trabajados;
    document.getElementById('repDiasDescanso').textContent = diasDescanso;
    document.getElementById('repDiasFalta').textContent = data.dias_falta;
    document.getElementById('repTotalDias').textContent = data.dias_en_mes;
    document.getElementById('repMinRetraso').textContent = data.total_minutos_retraso;
    document.getElementById('repMinExtra').textContent = data.total_minutos_extra;

    recalcularSalario();
}

function recalcularSalario() {
    if (!_reporteData) return;
    const sueldo = parseFloat(document.getElementById('reporteSueldo').value) || 0;
    const data = _reporteData;

    // Sueldo por minuto = sueldo / (dias_laborales * horas * 60)
    const diasLaborales = data.dias_en_mes - data.dias.filter(d => d.es_libre).length;
    const horasTurno = calcularHorasTurno(data.hora_entrada, data.hora_salida);
    const sueldoPorMinuto = diasLaborales > 0 ? sueldo / (diasLaborales * horasTurno * 60) : 0;

    const descRetraso = Math.round(data.total_minutos_retraso * sueldoPorMinuto * 100) / 100;
    const pagoExtra = Math.round(data.total_minutos_extra * sueldoPorMinuto * 100) / 100;
    const descFaltas = Math.round(data.dias_falta * (sueldo / diasLaborales) * 100) / 100;
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
    // Don't edit if already editing
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

        // Get current values for the other field
        const row = td.closest('tr');
        const cells = row.querySelectorAll('.cell-editable');
        let hora_ingreso, hora_salida;

        if (tipo === 'ingreso') {
            hora_ingreso = nuevoValor || null;
            // Get salida from the other cell
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
            const resp = await fetch(`${API_URL}/api/personal/asistencia-manual`, {
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
                cargarReporte(); // Reload
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

// ============ ROL DE LIBRES ============
const MAX_POR_DIA = 3;
const MESES_NOMBRE = ['ENERO','FEBRERO','MARZO','ABRIL','MAYO','JUNIO','JULIO','AGOSTO','SEPTIEMBRE','OCTUBRE','NOVIEMBRE','DICIEMBRE'];
const DIAS_SEMANA_MAP = { 0:'domingo', 1:'lunes', 2:'martes', 3:'miercoles', 4:'jueves', 5:'viernes', 6:'sabado' };
// Grid column index (0=Mon..6=Sun) to dia name
const COL_TO_DIA = ['lunes','martes','miercoles','jueves','viernes','sabado','domingo'];

// rolAssigned: { personalId: 'dia_nombre' } - tracks who is placed in the calendar
// Starts EMPTY - user drags everyone, then saves on PDF download
let rolAssigned = {};
let _rolPersonal = [];
let _rolMes = 0;
let _rolAnio = 2026;
let _rolSaved = false; // true once user has saved/printed

// Set default month to current
(function() {
    const now = new Date();
    document.getElementById('rolMes').value = now.getMonth();
    document.getElementById('rolAnio').value = now.getFullYear();
})();

// Get all dateStr for a given weekday column in current month
function getDatesForColumn(colIndex) {
    const firstDay = new Date(_rolAnio, _rolMes, 1);
    const lastDay = new Date(_rolAnio, _rolMes + 1, 0);
    const totalDays = lastDay.getDate();
    const dates = [];
    for (let d = 1; d <= totalDays; d++) {
        const dt = new Date(_rolAnio, _rolMes, d);
        let dow = dt.getDay(); // 0=Sun
        dow = (dow === 0) ? 6 : dow - 1; // Mon=0..Sun=6
        if (dow === colIndex) {
            dates.push(`${_rolAnio}-${String(_rolMes+1).padStart(2,'0')}-${String(d).padStart(2,'0')}`);
        }
    }
    return dates;
}

// Get column index (0=Mon..6=Sun) from a dateStr
function getColFromDate(dateStr) {
    const dt = new Date(dateStr + 'T00:00:00');
    let dow = dt.getDay();
    return (dow === 0) ? 6 : dow - 1;
}

// Build sidebar - hide people already placed in calendar
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
                ${p.nombre} ${p.apellido}
                <div class="drag-cargo">${cargo}</div>
            </div>
        </div>`;
    }).join('');

    // Attach drag events
    list.querySelectorAll('.rol-drag-item:not(.placed)').forEach(item => {
        item.addEventListener('dragstart', (e) => {
            e.dataTransfer.setData('text/plain', item.dataset.pid);
            e.dataTransfer.effectAllowed = 'copy';
            item.style.opacity = '0.5';
            // Highlight entire column on dragover
        });
        item.addEventListener('dragend', (e) => {
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

    // Fetch all active personnel
    try {
        const resp = await fetch(`${API_URL}/api/personal/?activos=true&limit=200`);
        if (resp.ok) _rolPersonal = await resp.json();
    } catch(e) { console.error(e); }

    // Calendar starts empty - user assigns days by dragging

    // Build sidebar (hides placed people)
    buildRolSidebar(_rolPersonal);

    // Build map: day-of-week -> list of personnel assigned to that day
    const libresPorDia = {};
    for (const [pid, dia] of Object.entries(rolAssigned)) {
        if (!libresPorDia[dia]) libresPorDia[dia] = [];
        const person = _rolPersonal.find(p => p.id === parseInt(pid));
        if (person) libresPorDia[dia].push(person);
    }

    // Calendar logic
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
                        ${p.nombre} ${p.apellido}
                        <span class="chip-cargo">${cargo}</span>
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

    // Attach drop events to all calendar cells
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
            // Only clear if leaving the cell entirely
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

// Highlight all cells in a column
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

// Add person to entire weekday column (no DB save yet)
function agregarAlColumna(colIndex, personalId) {
    const diaName = COL_TO_DIA[colIndex];

    // Count how many are already on this day
    const currentCount = Object.entries(rolAssigned).filter(([pid, dia]) => {
        return dia === diaName && _rolPersonal.find(p => p.id === parseInt(pid));
    }).length;

    if (currentCount >= MAX_POR_DIA) {
        mostrarAlerta(`Maximo ${MAX_POR_DIA} personas por dia (${diaName})`, 'error');
        return;
    }

    // Check if already assigned to this day
    if (rolAssigned[personalId] === diaName) {
        mostrarAlerta('Esta persona ya tiene libre este dia', 'warning');
        return;
    }

    // Assign to this weekday column (only in memory)
    rolAssigned[personalId] = diaName;
    generarRolLibres();
}

// Remove person from entire column (all weeks)
function quitarDelRol(personalId) {
    delete rolAssigned[personalId];
    generarRolLibres();
}

// Save all assignments to DB, then print PDF
async function descargarRolPDF() {
    // Save each person's dia_libre to the database
    const updates = Object.entries(rolAssigned).map(([pid, dia]) => {
        return fetch(`${API_URL}/api/personal/${pid}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ dia_libre: dia })
        });
    });

    try {
        await Promise.all(updates);
        _rolSaved = true;
        mostrarAlerta('Dias libres guardados correctamente', 'success');
    } catch(e) {
        mostrarAlerta('Error al guardar algunos dias libres', 'error');
    }

    // Small delay so the alert shows, then print
    setTimeout(() => {
        window.print();
    }, 300);
}
