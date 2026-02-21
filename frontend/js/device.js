// ============ DEVICE CONNECTION & CONFIG ============
async function cargarConfigEnLogin() {
    try {
        const response = await apiFetch(`${API_URL}/api/zkteco/config`);
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
        await apiFetch(`${API_URL}/api/zkteco/configurar-ip`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ip, puerto, password })
        });

        const response = await apiFetch(`${API_URL}/api/zkteco/test-conexion`);
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
    cargarNombreSucursal();
    mostrarUsuarioNavbar();
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
    cargarNombreSucursal();
    mostrarUsuarioNavbar();
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
        const response = await apiFetch(`${API_URL}/api/zkteco/test-conexion`);
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
        const response = await apiFetch(`${API_URL}/api/zkteco/config`);
        if (response.ok) {
            const config = await response.json();
            const ipEl     = document.getElementById('ipZkteco');
            const puertoEl = document.getElementById('puertoZkteco');
            const passEl   = document.getElementById('passwordZkteco');
            const infoEl   = document.getElementById('configInfo');
            if (ipEl)     ipEl.value     = config.ip || '';
            if (puertoEl) puertoEl.value = config.puerto || 4370;
            if (passEl)   passEl.value   = config.password || 0;
            if (infoEl && config.guardado) {
                infoEl.innerHTML =
                    `<strong>Dispositivo configurado</strong> &mdash; ${escapeHtml(config.ip)}:${escapeHtml(String(config.puerto))}`;
            }
        }
    } catch (error) {
        console.error('Error cargando config:', error);
    }
}

async function cargarNombreSucursal() {
    try {
        const resp = await apiFetch(`${API_URL}/api/sucursal`);
        if (resp.ok) {
            const data = await resp.json();
            const brand = document.querySelector('.navbar-brand');
            if (brand && data.nombre) {
                brand.innerHTML = `&#9881; ${escapeHtml(data.nombre)} <span>| ZKTeco</span>`;
            }
        }
    } catch (e) { /* ignore */ }
}

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
        const response = await apiFetch(`${API_URL}/api/zkteco/configurar-ip`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ip, puerto, password })
        });
        const data = await response.json();
        if (response.ok) {
            statusDiv.innerHTML = `<div class="alert alert-success" style="margin-top:12px;">Configuracion guardada: ${escapeHtml(ip)}:${escapeHtml(puerto)}</div>`;
            document.getElementById('configInfo').innerHTML =
                `<strong>Dispositivo configurado</strong> &mdash; ${escapeHtml(ip)}:${escapeHtml(puerto)}`;
        } else {
            statusDiv.innerHTML = `<div class="alert alert-error" style="margin-top:12px;">${escapeHtml(data.detail || 'Error')}</div>`;
        }
    } catch (error) {
        statusDiv.innerHTML = `<div class="alert alert-error" style="margin-top:12px;">${escapeHtml(error.message)}</div>`;
    }
}

async function testConexion() {
    await configurarIP();
    const statusDiv = document.getElementById('conexionStatus');
    statusDiv.innerHTML = '<div style="margin-top:12px;color:var(--slate-500);font-size:0.85rem;"><span class="spinner"></span> Probando conexion...</div>';

    try {
        const response = await apiFetch(`${API_URL}/api/zkteco/test-conexion`);
        const data = await response.json();

        if (response.ok) {
            const info = data.info;
            statusDiv.innerHTML = `
                <div class="alert alert-success" style="margin-top:12px;">
                    <strong>Conexion exitosa</strong><br>
                    Dispositivo: ${escapeHtml(info.nombre_dispositivo || 'ZKTeco')}<br>
                    Serial: ${escapeHtml(info.serial_number || '-')} | MAC: ${escapeHtml(info.mac || '-')}<br>
                    Usuarios: ${escapeHtml(info.usuarios_registrados || 0)} / ${escapeHtml(info.capacidad_usuarios || '-')}<br>
                    Huellas: ${escapeHtml(info.huellas_registradas || 0)} / ${escapeHtml(info.capacidad_huellas || '-')}<br>
                    Registros: ${escapeHtml(info.registros_asistencia || 0)}
                </div>
            `;
            refrescarEstadoDispositivo();
        } else {
            statusDiv.innerHTML = `<div class="alert alert-error" style="margin-top:12px;">${escapeHtml(data.detail || 'Error de conexion')}</div>`;
        }
    } catch (error) {
        statusDiv.innerHTML = `<div class="alert alert-error" style="margin-top:12px;">${escapeHtml(error.message)}</div>`;
    }
}

async function sincronizarUsuarios() {
    const statusDiv = document.getElementById('syncStatus');
    statusDiv.innerHTML = '<div style="margin-top:12px;color:var(--slate-500);font-size:0.85rem;"><span class="spinner"></span> Importando usuarios...</div>';

    try {
        const response = await apiFetch(`${API_URL}/api/zkteco/sincronizar-usuarios`, { method: 'POST' });
        const data = await response.json();

        if (response.ok) {
            statusDiv.innerHTML = `
                <div class="alert alert-success" style="margin-top:12px;">
                    <strong>Usuarios importados</strong><br>
                    Nuevos: ${escapeHtml(data.total_sincronizados)} | Actualizados: ${escapeHtml(data.total_actualizados || 0)}<br>
                    Total en dispositivo: ${escapeHtml(data.total_en_dispositivo)}
                </div>
            `;
            cargarPersonal();
            cargarEstadisticas();
        } else {
            statusDiv.innerHTML = `<div class="alert alert-error" style="margin-top:12px;">${escapeHtml(data.detail || 'Error')}</div>`;
        }
    } catch (error) {
        statusDiv.innerHTML = `<div class="alert alert-error" style="margin-top:12px;">${escapeHtml(error.message)}</div>`;
    }
}
