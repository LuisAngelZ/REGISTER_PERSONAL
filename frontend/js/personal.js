// ============ CREAR PERSONAL ============
async function crearPersonal(event) {
    event.preventDefault();
    const btn = event.submitter || event.target.querySelector('button[type="submit"]');

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

    if (btn) btnLoading(btn, true);
    try {
        const response = await apiFetch(`${API_URL}/api/personal/`, {
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
                const expRes = await apiFetch(`${API_URL}/api/zkteco/exportar-usuario`, {
                    method: 'POST',
                    headers: apiHeaders(),
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
    } finally {
        if (btn) btnLoading(btn, false);
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
        const response = await apiFetch(`${API_URL}/api/personal/${id}`);
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
    const btn = event.submitter || event.target.querySelector('button[type="submit"]');

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

    if (btn) btnLoading(btn, true);
    try {
        const response = await apiFetch(`${API_URL}/api/personal/${personalActual.id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(datos)
        });

        if (!response.ok) throw new Error('Error al actualizar');
        mostrarAlerta('Personal actualizado', 'success');

        if (dispositivoConectado && personalActual.id) {
            try {
                const expRes = await apiFetch(`${API_URL}/api/zkteco/exportar-usuario`, {
                    method: 'POST',
                    headers: apiHeaders(),
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
    } finally {
        if (btn) btnLoading(btn, false);
    }
}

function cancelarEdicion() {
    document.getElementById('formEditar').style.display = 'none';
    document.getElementById('buscarId').value = '';
    personalActual = null;
}

// ============ CARGAR PERSONAL (CARDS) ============
const ITEMS_PER_PAGE = 12;
let _currentPage = 1;

async function cargarPersonal(page) {
    if (page !== undefined) _currentPage = page;

    try {
        const response = await apiFetch(`${API_URL}/api/personal/`);
        if (!response.ok) throw new Error('Error al cargar personal');

        const personal = await response.json();
        const container = document.getElementById('personnelContainer');
        const pagDiv = document.getElementById('paginationControls');

        if (personal.length === 0) {
            container.innerHTML = `
                <div class="empty-state" style="grid-column:1/-1;">
                    <div class="empty-icon">&#128100;</div>
                    <p>No hay personal registrado</p>
                </div>
            `;
            if (pagDiv) pagDiv.innerHTML = '';
            return;
        }

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
            if (pagDiv) pagDiv.innerHTML = '';
            return;
        }

        const totalPages = Math.ceil(filtered.length / ITEMS_PER_PAGE);
        if (_currentPage > totalPages) _currentPage = totalPages;
        if (_currentPage < 1) _currentPage = 1;

        const start = (_currentPage - 1) * ITEMS_PER_PAGE;
        const pageItems = filtered.slice(start, start + ITEMS_PER_PAGE);

        const DURACION_LABEL = {'3_meses':'3 Meses','6_meses':'6 Meses','1_anio':'1 Ano'};

        container.innerHTML = pageItems.map(p => {
            const initials = escapeHtml((p.nombre[0] || '') + (p.apellido[0] || ''));
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
                    <div class="person-name">${escapeHtml(p.nombre)} ${escapeHtml(p.apellido)}</div>
                    <div class="person-meta">
                        <span>&#128179; CI: ${escapeHtml(p.documento)}</span>
                        <span>&#128188; ${escapeHtml(puestoLabel)}</span>
                        <span>&#128197; ${escapeHtml(fechaInicioStr)} - ${escapeHtml(fechaFinStr)}</span>
                        <span>&#127774; Libre: ${escapeHtml(diaLibreLabel)}</span>
                    </div>
                    <div class="person-tags">
                        <span class="tag">${escapeHtml(turnoLabel)}</span>
                        <span class="tag">${escapeHtml(duracionLabel)}</span>
                        ${p.user_id ? `<span class="tag uid">ID: ${escapeHtml(String(p.user_id))}</span>` : ''}
                    </div>
                    <div class="person-actions">
                        <button class="btn btn-sm btn-success" onclick="editarPersonal(${p.id})">Editar</button>
                        <button class="btn btn-sm btn-info" onclick="verAsistencia(${p.id})">Asistencia</button>
                        <button class="btn btn-sm btn-danger" onclick="eliminarPersonal(${p.id})">Eliminar</button>
                    </div>
                </div>
            `;
        }).join('');

        // Pagination controls
        if (pagDiv && totalPages > 1) {
            let pagHtml = `<span class="page-info">${filtered.length} registros - Pag ${_currentPage}/${totalPages}</span>`;
            pagHtml += `<button class="btn btn-sm btn-ghost" onclick="cargarPersonal(1)" ${_currentPage === 1 ? 'disabled' : ''}>&laquo;</button>`;
            pagHtml += `<button class="btn btn-sm btn-ghost" onclick="cargarPersonal(${_currentPage - 1})" ${_currentPage === 1 ? 'disabled' : ''}>&lsaquo;</button>`;

            const maxButtons = 5;
            let startPage = Math.max(1, _currentPage - Math.floor(maxButtons / 2));
            let endPage = Math.min(totalPages, startPage + maxButtons - 1);
            if (endPage - startPage < maxButtons - 1) startPage = Math.max(1, endPage - maxButtons + 1);

            for (let i = startPage; i <= endPage; i++) {
                pagHtml += `<button class="btn btn-sm ${i === _currentPage ? 'btn-primary' : 'btn-ghost'}" onclick="cargarPersonal(${i})">${i}</button>`;
            }

            pagHtml += `<button class="btn btn-sm btn-ghost" onclick="cargarPersonal(${_currentPage + 1})" ${_currentPage === totalPages ? 'disabled' : ''}>&rsaquo;</button>`;
            pagHtml += `<button class="btn btn-sm btn-ghost" onclick="cargarPersonal(${totalPages})" ${_currentPage === totalPages ? 'disabled' : ''}>&raquo;</button>`;
            pagDiv.innerHTML = pagHtml;
        } else if (pagDiv) {
            pagDiv.innerHTML = filtered.length > 0 ? `<span class="page-info">${filtered.length} registros</span>` : '';
        }

    } catch (error) {
        mostrarAlerta(error.message, 'error');
    }
}

function editarPersonal(id) {
    document.getElementById('buscarId').value = id;
    buscarPersonal();
    document.querySelectorAll('.section').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
    document.getElementById('editar-section').classList.add('active');
    document.querySelectorAll('.nav-item')[2].classList.add('active');
}

// ============ ELIMINAR ============
function eliminarPersonal(id) {
    confirmar(
        'Desactivar Personal',
        'Este personal sera desactivado del sistema. Puedes reactivarlo despues.',
        async () => {
            try {
                const response = await apiFetch(`${API_URL}/api/personal/${id}`, { method: 'DELETE' });
                if (!response.ok) throw new Error('Error al eliminar');
                mostrarAlerta('Personal desactivado', 'success');
                cargarPersonal();
                cargarEstadisticas();
            } catch (error) {
                mostrarAlerta(error.message, 'error');
            }
        }
    );
}

// ============ EXPORTAR LISTA ============
function exportarListaPersonal(formato) {
    const url = `${API_URL}/api/personal/exportar-lista?formato=${formato}`;
    window.open(url, '_blank');
}

// ============ ESTADISTICAS ============
async function cargarEstadisticas() {
    try {
        const response = await apiFetch(`${API_URL}/api/personal/stats/total`);
        if (!response.ok) throw new Error('Error');
        const stats = await response.json();
        document.getElementById('totalPersonal').textContent = stats.total;
        document.getElementById('activosPersonal').textContent = stats.activos;
        document.getElementById('inactivosPersonal').textContent = stats.inactivos;
    } catch (error) {
        console.error(error);
    }
}

// ============ VER ASISTENCIA ============
async function verAsistencia(personalId) {
    try {
        if (dispositivoConectado) {
            mostrarAlerta('Sincronizando asistencia...', 'info');
            try {
                await apiFetch(`${API_URL}/api/zkteco/sincronizar-registros`, { method: 'POST' });
            } catch (syncErr) {
                console.warn('Sync error:', syncErr);
            }
        }

        const response = await apiFetch(`${API_URL}/api/personal/${personalId}/asistencia?limit=500`);
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
                    <h2>${escapeHtml(data.nombre)}</h2>
                    <p>${escapeHtml(data.total_registros)} registros de asistencia</p>
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
