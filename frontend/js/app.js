// ============ INIT ============
// Módulos cargados antes de este archivo:
// helpers.js, auth.js, device.js, personal.js, dashboard.js, reporte.js, rol.js

window.addEventListener('load', async () => {
    await obtenerCsrfToken();
    await verificarAuth();
});

async function verificarAuth() {
    try {
        const resp = await apiFetch(`${API_URL}/api/auth/check`);
        const data = await resp.json();

        if (data.auth_required) {
            document.getElementById('authScreen').style.display = 'flex';
            document.getElementById('loginScreen').style.display = 'none';
        } else {
            document.getElementById('authScreen').style.display = 'none';
            document.getElementById('loginScreen').style.display = 'flex';
            await cargarConfigEnLogin();
        }
    } catch (error) {
        document.getElementById('loginScreen').style.display = 'flex';
        await cargarConfigEnLogin();
    }
}
