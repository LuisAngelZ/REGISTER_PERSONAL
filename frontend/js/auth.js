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
