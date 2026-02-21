// ============ INIT ============
// Módulos cargados antes de este archivo:
// helpers.js, auth.js, device.js, personal.js, dashboard.js, reporte.js, rol.js

async function cargarPartials() {
    const partials = [
        { id: 'personal',       file: 'personal' },
        { id: 'dashboard',      file: 'dashboard' },
        { id: 'registrar',      file: 'registrar' },
        { id: 'editar-section', file: 'editar' },
        { id: 'reporte',        file: 'reporte' },
        { id: 'configuracion',  file: 'configuracion' },
        { id: 'rol-libres',     file: 'rol-libres' },
    ];
    await Promise.all(partials.map(async ({ id, file }) => {
        try {
            const resp = await fetch(`/static/partials/${file}.html`);
            if (!resp.ok) {
                console.error(`[partials] ERROR ${resp.status} al cargar ${file}.html`);
                return;
            }
            const html = await resp.text();
            const el = document.getElementById(id);
            if (el) el.innerHTML = html;
        } catch (e) {
            console.error(`[partials] Fallo al cargar ${file}.html:`, e);
        }
    }));
}

window.addEventListener('load', async () => {
    await cargarPartials();
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
