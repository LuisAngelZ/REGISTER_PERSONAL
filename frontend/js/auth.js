// ============ AUTH ============
function toggleRegistro() {
    _modoRegistro = !_modoRegistro;
    const fields = document.getElementById('authRegistroFields');
    const btn = document.getElementById('btnAuth');
    const toggleBtn = document.getElementById('btnToggleRegistro');
    const title = document.getElementById('authTitle');
    const subtitle = document.getElementById('authSubtitle');

    if (_modoRegistro) {
        fields.style.display = 'block';
        btn.textContent = 'Crear Cuenta';
        btn.onclick = registrarUsuario;
        toggleBtn.textContent = 'Ya tengo cuenta';
        title.textContent = 'Crear Cuenta';
        subtitle.textContent = 'Registra un nuevo usuario';
    } else {
        fields.style.display = 'none';
        btn.textContent = 'Ingresar';
        btn.onclick = loginUsuario;
        toggleBtn.textContent = 'Crear cuenta nueva';
        title.textContent = 'Iniciar Sesion';
        subtitle.textContent = 'Ingresa tus credenciales';
    }
}

async function loginUsuario() {
    const username = document.getElementById('authUsername').value.trim();
    const password = document.getElementById('authPassword').value;
    const statusDiv = document.getElementById('authStatus');

    if (!username || !password) {
        statusDiv.className = 'login-status error';
        statusDiv.textContent = 'Completa usuario y password';
        return;
    }

    statusDiv.className = 'login-status conectando';
    statusDiv.innerHTML = '<span class="spinner"></span> Verificando...';

    try {
        const resp = await fetch(`${API_URL}/api/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        const data = await resp.json();

        if (resp.ok) {
            usuarioActual = data.usuario;
            statusDiv.className = 'login-status success';
            statusDiv.textContent = `Bienvenido, ${data.usuario.nombre}!`;
            setTimeout(() => {
                document.getElementById('authScreen').style.display = 'none';
                document.getElementById('loginScreen').style.display = 'flex';
                document.getElementById('loginUserInfo').textContent = `Sesion: ${data.usuario.nombre} (${data.usuario.rol})`;
                cargarConfigEnLogin();
            }, 600);
        } else {
            statusDiv.className = 'login-status error';
            statusDiv.textContent = data.detail || 'Usuario o password incorrectos';
        }
    } catch (error) {
        statusDiv.className = 'login-status error';
        statusDiv.textContent = 'Error de conexion con el servidor';
    }
}

async function registrarUsuario() {
    const username = document.getElementById('authUsername').value.trim();
    const password = document.getElementById('authPassword').value;
    const nombre = document.getElementById('authNombre').value.trim();
    const statusDiv = document.getElementById('authStatus');

    if (!username || !password || !nombre) {
        statusDiv.className = 'login-status error';
        statusDiv.textContent = 'Completa todos los campos';
        return;
    }

    if (password.length < 8) {
        statusDiv.className = 'login-status error';
        statusDiv.textContent = 'Password debe tener al menos 8 caracteres';
        return;
    }

    statusDiv.className = 'login-status conectando';
    statusDiv.innerHTML = '<span class="spinner"></span> Creando cuenta...';

    try {
        const resp = await fetch(`${API_URL}/api/auth/registro`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password, nombre, rol: 'admin' })
        });
        const data = await resp.json();

        if (resp.ok) {
            statusDiv.className = 'login-status success';
            statusDiv.textContent = 'Cuenta creada! Iniciando sesion...';
            setTimeout(() => {
                _modoRegistro = false;
                toggleRegistro();
                loginUsuario();
            }, 800);
        } else {
            statusDiv.className = 'login-status error';
            statusDiv.textContent = data.detail || 'Error al crear cuenta';
        }
    } catch (error) {
        statusDiv.className = 'login-status error';
        statusDiv.textContent = 'Error de conexion con el servidor';
    }
}

function mostrarUsuarioNavbar() {
    if (usuarioActual) {
        document.getElementById('navUserInfo').textContent = escapeHtml(usuarioActual.nombre);
        document.getElementById('btnLogout').style.display = 'inline-block';
    }
}

function cerrarSesion() {
    usuarioActual = null;
    document.getElementById('mainApp').classList.remove('visible');
    document.getElementById('loginScreen').style.display = 'none';
    document.getElementById('authScreen').style.display = 'flex';
    document.getElementById('authUsername').value = '';
    document.getElementById('authPassword').value = '';
    document.getElementById('authStatus').className = 'login-status';
    document.getElementById('authStatus').textContent = '';
    document.getElementById('navUserInfo').textContent = '';
    document.getElementById('btnLogout').style.display = 'none';
}

// ============ CAMBIAR PASSWORD ============
async function cambiarPassword() {
    const username = document.getElementById('cpUsername').value.trim();
    const actual = document.getElementById('cpActual').value;
    const nuevo = document.getElementById('cpNuevo').value;
    const statusDiv = document.getElementById('cpStatus');

    if (!username || !actual || !nuevo) {
        statusDiv.className = 'connection-status error'; statusDiv.textContent = 'Completa todos los campos'; return;
    }
    if (nuevo.length < 8) {
        statusDiv.className = 'connection-status error'; statusDiv.textContent = 'El nuevo password debe tener al menos 8 caracteres'; return;
    }

    statusDiv.className = 'connection-status conectando'; statusDiv.innerHTML = '<span class="spinner"></span> Cambiando...';
    try {
        const resp = await apiFetch(`${API_URL}/api/auth/cambiar-password`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password_actual: actual, password_nuevo: nuevo })
        });
        const data = await resp.json();
        if (resp.ok) {
            statusDiv.className = 'connection-status success'; statusDiv.textContent = 'Password cambiado correctamente';
            document.getElementById('cpActual').value = '';
            document.getElementById('cpNuevo').value = '';
        } else {
            statusDiv.className = 'connection-status error'; statusDiv.textContent = data.detail || 'Error al cambiar password';
        }
    } catch(e) {
        statusDiv.className = 'connection-status error'; statusDiv.textContent = 'Error de conexion';
    }
}

// ============ GESTION DE USUARIOS ============
async function cargarUsuariosSistema() {
    const container = document.getElementById('usuariosSistemaContainer');
    container.innerHTML = '<span class="spinner"></span>';
    try {
        const resp = await apiFetch(`${API_URL}/api/auth/usuarios`);
        if (!resp.ok) throw new Error('Error al cargar usuarios');
        const usuarios = await resp.json();
        if (!usuarios.length) {
            container.innerHTML = '<p style="color:var(--slate-400);font-size:0.85rem;">No hay usuarios registrados</p>';
            return;
        }
        container.innerHTML = `<table style="width:100%;border-collapse:collapse;font-size:0.85rem;">
            <thead><tr style="background:var(--slate-100);">
                <th style="padding:8px 12px;text-align:left;">Usuario</th>
                <th style="padding:8px 12px;text-align:left;">Nombre</th>
                <th style="padding:8px 12px;text-align:left;">Rol</th>
                <th style="padding:8px 12px;text-align:left;">Estado</th>
                <th style="padding:8px 12px;"></th>
            </tr></thead>
            <tbody>${usuarios.map(u => `
                <tr style="border-top:1px solid var(--slate-200);">
                    <td style="padding:8px 12px;">${escapeHtml(u.username)}</td>
                    <td style="padding:8px 12px;">${escapeHtml(u.nombre)}</td>
                    <td style="padding:8px 12px;"><span class="tag">${escapeHtml(u.rol)}</span></td>
                    <td style="padding:8px 12px;"><span class="person-status ${u.activo ? 'active' : 'inactive'}">${u.activo ? 'Activo' : 'Inactivo'}</span></td>
                    <td style="padding:8px 12px;">
                        ${u.activo ? `<button class="btn btn-sm btn-danger" onclick="desactivarUsuario(${u.id},'${escapeHtml(u.username)}')">Desactivar</button>` : ''}
                    </td>
                </tr>`).join('')}
            </tbody>
        </table>`;
    } catch(e) {
        container.innerHTML = `<p style="color:var(--danger);font-size:0.85rem;">${escapeHtml(e.message)}</p>`;
    }
}

function desactivarUsuario(id, username) {
    confirmar('Desactivar Usuario', `Desactivar el usuario "${username}" del sistema?`, async () => {
        try {
            const resp = await apiFetch(`${API_URL}/api/auth/usuarios/${id}`, { method: 'DELETE' });
            const data = await resp.json();
            if (resp.ok) {
                mostrarAlerta(data.mensaje, 'success');
                cargarUsuariosSistema();
            } else {
                mostrarAlerta(data.detail || 'Error al desactivar', 'error');
            }
        } catch(e) {
            mostrarAlerta('Error de conexion', 'error');
        }
    });
}
