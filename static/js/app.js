const API_BASE = "/api";

// Estado local para el panel administrativo
let pedidosMemoria = [];
let filtroActual = "todos";

// ---------------------------------------------------------------------
// Utilidades de Renderizado Visual (Tarjetas y Recibos)
// ---------------------------------------------------------------------
const formatearMoneda = (val) => `$${(val || 0).toLocaleString("es-CO")}`;

function pintarResultado(obj) {
    const el = document.getElementById("resultado");

    // Si viene un error de la API
    if (obj.error) {
        el.innerHTML = `
            <div style="background: rgba(239, 68, 68, 0.15); border: 1px solid #ef4444; color: #fca5a5; padding: 12px; border-radius: 8px;">
                <strong>⚠️ Error:</strong> ${obj.error}
            </div>
        `;
        return;
    }

    // Generar lista de ítems / productos
    const itemsHTML = (obj.items || []).map(item => `
        <div style="display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px dashed #334155; font-size: 0.9rem;">
            <span><strong>${item.producto.replace('_', ' ')}</strong> (x${item.cantidad})</span>
            <span style="color: #38bdf8;">${formatearMoneda(item.precio_unitario * item.cantidad)}</span>
        </div>
    `).join('');

    // Color según el estado del pedido
    let estadoColor = '#f59e0b'; // Pendiente (Naranja)
    if (obj.estado === 'pagado') estadoColor = '#10b981'; // Verde
    if (obj.estado === 'enviado') estadoColor = '#06b6d4'; // Azul

    // Construir la tarjeta visual del pedido
    el.innerHTML = `
        <div style="background: #1e293b; border: 1px solid #334155; border-radius: 10px; padding: 20px; color: #f8fafc; font-family: sans-serif;">
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #334155; padding-bottom: 12px; margin-bottom: 15px;">
                <div>
                    <h3 style="margin: 0; color: #38bdf8; font-size: 1.25rem;">Pedido #${obj.id || 'Nuevo'}</h3>
                    <p style="margin: 4px 0 0 0; color: #94a3b8; font-size: 0.9rem;">👤 <strong>Cliente:</strong> ${obj.cliente}</p>
                </div>
                <span style="background: ${estadoColor}; color: #0f172a; font-weight: bold; padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; text-transform: uppercase;">
                    ${obj.estado || 'Procesado'}
                </span>
            </div>

            <div style="margin-bottom: 15px;">
                <h4 style="margin: 0 0 8px 0; font-size: 0.95rem; color: #cbd5e1; text-transform: uppercase; letter-spacing: 0.5px;">Resumen de Productos:</h4>
                ${itemsHTML}
            </div>

            <div style="background: #0f172a; padding: 12px; border-radius: 8px; font-size: 0.9rem;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 4px; color: #94a3b8;">
                    <span>Subtotal:</span>
                    <span style="color: #f8fafc;">${formatearMoneda(obj.subtotal)}</span>
                </div>
                ${obj.descuento > 0 ? `
                    <div style="display: flex; justify-content: space-between; margin-bottom: 4px; color: #f43f5e;">
                        <span>Descuento (${obj.cupon || 'Cupón'}):</span>
                        <span>-${formatearMoneda(obj.descuento)}</span>
                    </div>
                ` : ''}
                <div style="display: flex; justify-content: space-between; margin-bottom: 4px; color: #94a3b8;">
                    <span>Empaque de regalo:</span>
                    <span style="color: #f8fafc;">${formatearMoneda(obj.costo_empaque)}</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px; color: #94a3b8;">
                    <span>Envío (${obj.tipo_envio || 'Estándar'}):</span>
                    <span style="color: #f8fafc;">${formatearMoneda(obj.costo_envio)}</span>
                </div>

                <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #334155; padding-top: 10px; font-size: 1.1rem; font-weight: bold;">
                    <span>Total Final:</span>
                    <span style="color: #38bdf8; font-size: 1.2rem;">${formatearMoneda(obj.total)}</span>
                </div>
            </div>

            ${obj.metodo_pago ? `
                <div style="margin-top: 12px; font-size: 0.85rem; color: #94a3b8; text-align: right;">
                    💳 <strong>Método de pago:</strong> ${obj.metodo_pago.toUpperCase()}
                </div>
            ` : ''}
        </div>
    `;
}

async function llamarApi(path, method = "GET", body = null) {
    const opts = { method, headers: { "Content-Type": "application/json" } };
    if (body) opts.body = JSON.stringify(body);
    const resp = await fetch(`${API_BASE}${path}`, opts);
    const data = await resp.json();
    if (!resp.ok) {
        throw new Error(data.detail || "Error desconocido");
    }
    return data;
}

// ---------------------------------------------------------------------
// Formulario: agregar / quitar productos dinámicamente
// ---------------------------------------------------------------------
const HTML_ITEM_ROW = `
    <select class="item-marca">
        <option value="lattafa_sublime">Lattafa Sublime</option>
        <option value="blue_chanel">Blue Chanel</option>
        <option value="summer_hammer">Summer Hammer</option>
        <option value="lacoste_white">Lacoste White</option>
        <option value="one_million">One Million</option>
        <option value="aventus_creed">Aventus Creed</option>
        <option value="invictus">Invictus</option>
        <option value="legend_montblanc">Legend Montblanc</option>
        <option value="212_vip">212 VIP</option>
    </select>
    <select class="item-tamano">
        <option value="30ml" data-precio="15000">30ml — $15.000</option>
        <option value="50ml" data-precio="35000">50ml — $35.000</option>
        <option value="100ml" data-precio="45000">100ml — $45.000</option>
    </select>
    <input type="number" class="item-cantidad" min="1" value="1" placeholder="Cantidad">
    <input type="number" class="item-precio" min="1" value="15000" placeholder="Precio unitario" readonly>
    <button type="button" class="btn-remove-item" title="Quitar">✕</button>
`;

function activarAutoprecio(row) {
    const selectTamano = row.querySelector(".item-tamano");
    const inputPrecio = row.querySelector(".item-precio");

    const actualizarPrecioUnitario = () => {
        const precioUnitario = parseFloat(selectTamano.selectedOptions[0].dataset.precio || 0);
        inputPrecio.value = precioUnitario;
    };

    selectTamano.addEventListener("change", actualizarPrecioUnitario);
    actualizarPrecioUnitario();
}

document.getElementById("btn-add-item").addEventListener("click", () => {
    const container = document.getElementById("items-container");
    const row = document.createElement("div");
    row.className = "item-row";
    row.innerHTML = HTML_ITEM_ROW;
    row.querySelector(".btn-remove-item").addEventListener("click", () => row.remove());
    activarAutoprecio(row);
    container.appendChild(row);
});

document.querySelectorAll(".btn-remove-item").forEach((btn) => {
    btn.addEventListener("click", (e) => e.target.closest(".item-row").remove());
});

// Activar el autoprecio también en la fila inicial del HTML
document.querySelectorAll(".item-row").forEach(activarAutoprecio);

// ---------------------------------------------------------------------
// Crear pedido (Builder & Decorators)
// ---------------------------------------------------------------------
document.getElementById("form-pedido").addEventListener("submit", async (e) => {
    e.preventDefault();

    const items = Array.from(document.querySelectorAll(".item-row")).map((row) => {
        const marca = row.querySelector(".item-marca").value;
        const selectTamano = row.querySelector(".item-tamano");
        const tamano = selectTamano.value;
        const precioUnitarioReal = parseFloat(selectTamano.selectedOptions[0].dataset.precio || 0);

        return {
            producto: `${marca}_${tamano}`,
            cantidad: parseInt(row.querySelector(".item-cantidad").value, 10),
            precio_unitario: precioUnitarioReal,
        };
    });

    const payload = {
        cliente: document.getElementById("cliente").value,
        items,
        tipo_envio: document.getElementById("tipo_envio").value,
        cupon: document.getElementById("cupon").value || null,
        empaque_regalo: document.getElementById("empaque_regalo").checked,
    };

    try {
        const pedido = await llamarApi("/pedidos", "POST", payload);
        pintarResultado(pedido);
        document.getElementById("pedido_id_pago").value = pedido.id;
        document.getElementById("pedido_id_enviar").value = pedido.id;
        await cargarPedidos();
    } catch (err) {
        pintarResultado({ error: err.message });
    }
});

// ---------------------------------------------------------------------
// Campos dinámicos según método de pago (Factory Method)
// ---------------------------------------------------------------------
const CAMPOS_POR_METODO = {
    tarjeta: [{ id: "token_tarjeta", label: "Token de tarjeta", value: "tok_visa_123" }],
    nequi: [{ id: "telefono_nequi", label: "Teléfono de Nequi", value: "3001234567" }],
};

function renderCamposPago() {
    const metodo = document.getElementById("metodo_pago").value;
    const contenedor = document.getElementById("campos-pago");
    contenedor.innerHTML = "";
    for (const campo of CAMPOS_POR_METODO[metodo]) {
        const label = document.createElement("label");
        label.innerHTML = `${campo.label}<input type="text" id="${campo.id}" value="${campo.value}">`;
        contenedor.appendChild(label);
    }
}
document.getElementById("metodo_pago").addEventListener("change", renderCamposPago);
renderCamposPago();

// ---------------------------------------------------------------------
// Procesar pago (State & Factory)
// ---------------------------------------------------------------------
document.getElementById("form-pago").addEventListener("submit", async (e) => {
    e.preventDefault();
    const metodo = document.getElementById("metodo_pago").value;
    const payload = {
        pedido_id: parseInt(document.getElementById("pedido_id_pago").value, 10),
        metodo_pago: metodo,
    };
    for (const campo of CAMPOS_POR_METODO[metodo]) {
        payload[campo.id] = document.getElementById(campo.id).value;
    }

    try {
        const pedido = await llamarApi("/pagos", "POST", payload);
        pintarResultado(pedido);
        await cargarPedidos();
    } catch (err) {
        pintarResultado({ error: err.message });
    }
});

// ---------------------------------------------------------------------
// Marcar como enviado (State & Observer)
// ---------------------------------------------------------------------
document.getElementById("form-enviar").addEventListener("submit", async (e) => {
    e.preventDefault();
    const id = document.getElementById("pedido_id_enviar").value;
    try {
        const pedido = await llamarApi(`/pedidos/${id}/enviar`, "POST");
        pintarResultado(pedido);
        await cargarPedidos();
    } catch (err) {
        pintarResultado({ error: err.message });
    }
});

// ---------------------------------------------------------------------
// Panel Administrativo: Renderizado de Tabla, Filtros y Acciones
// ---------------------------------------------------------------------
function obtenerColorBadge(estado) {
    if (estado === "pagado") return "#10b981";  // Verde
    if (estado === "enviado") return "#06b6d4"; // Azul
    return "#f59e0b";                           // Naranja (Pendiente)
}

function renderizarTabla() {
    const tbody = document.getElementById("tabla-pedidos-body");
    if (!tbody) return;
    tbody.innerHTML = "";

    const pedidosFiltrados = pedidosMemoria.filter((p) => {
        if (filtroActual === "todos") return true;
        return p.estado === filtroActual;
    });

    if (pedidosFiltrados.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" style="text-align: center; padding: 24px; color: #64748b;">
                    No se encontraron pedidos con el estado seleccionado.
                </td>
            </tr>
        `;
        return;
    }

    pedidosFiltrados.forEach((p) => {
        const tr = document.createElement("tr");
        tr.style.borderBottom = "1px solid #334155";

        // Formato compacto de items para la tabla
        const itemsResumen = (p.items || [])
            .map(i => `${i.cantidad}x ${i.producto.split('_')[0]}`)
            .join(", ") || "Sin items";

        // Botón contextual según el estado
        let botonAccion = "";
        if (p.estado === "pendiente") {
            botonAccion = `
                <div style="display: flex; gap: 6px; justify-content: center; align-items: center;">
                    <button 
                        type="button" 
                        class="btn-primary btn-accion-cargar-pago" 
                        data-id="${p.id}" 
                        style="padding: 5px 12px; font-size: 0.8rem; cursor: pointer;">
                        💳 Cargar a Caja
                    </button>
                    <button 
                        type="button" 
                        class="btn-accion-eliminar" 
                        data-id="${p.id}" 
                        title="Cancelar y eliminar pedido"
                        style="padding: 5px 9px; font-size: 0.85rem; cursor: pointer; background: rgba(239, 68, 68, 0.2); border: 1px solid #ef4444; color: #fca5a5; border-radius: 4px;">
                        🗑️
                    </button>
                </div>
            `;
        } else if (p.estado === "pagado") {
            botonAccion = `
                <button 
                    type="button" 
                    class="btn-secondary btn-accion-despachar-directo" 
                    data-id="${p.id}" 
                    style="padding: 5px 12px; font-size: 0.8rem; border-color: #06b6d4; color: #38bdf8; cursor: pointer;">
                    🚚 Despachar
                </button>
            `;
        } else {
            botonAccion = `<span style="color: #64748b; font-size: 0.85rem; font-weight: 500;">✓ Concluido</span>`;
        }

        tr.innerHTML = `
            <td style="padding: 12px 8px; font-weight: bold; color: #38bdf8;">#${p.id}</td>
            <td style="padding: 12px 8px; font-weight: 500;">${p.cliente}</td>
            <td style="padding: 12px 8px; color: #94a3b8; font-size: 0.85rem;">${itemsResumen}</td>
            <td style="padding: 12px 8px; text-transform: capitalize;">${p.tipo_envio || "Estándar"}</td>
            <td style="padding: 12px 8px; font-weight: bold; color: #f8fafc;">${formatearMoneda(p.total)}</td>
            <td style="padding: 12px 8px;">
                <span style="background: ${obtenerColorBadge(p.estado)}; color: #0f172a; font-weight: bold; padding: 3px 10px; border-radius: 12px; font-size: 0.75rem; text-transform: uppercase;">
                    ${p.estado}
                </span>
            </td>
            <td style="padding: 12px 8px; text-align: center;">
                ${botonAccion}
            </td>
        `;

        tbody.appendChild(tr);
    });

    conectarBotonesAccion();
}

function conectarBotonesAccion() {
    // 1. Cargar datos del pedido directamente al formulario de pago
    document.querySelectorAll(".btn-accion-cargar-pago").forEach((btn) => {
        btn.addEventListener("click", () => {
            const pedidoId = btn.dataset.id;
            const inputIdPago = document.getElementById("pedido_id_pago");
            inputIdPago.value = pedidoId;
            inputIdPago.scrollIntoView({ behavior: "smooth", block: "center" });
            inputIdPago.focus();
        });
    });

    // 2. Despachar el pedido directamente desde la fila
    document.querySelectorAll(".btn-accion-despachar-directo").forEach((btn) => {
        btn.addEventListener("click", async () => {
            const pedidoId = btn.dataset.id;
            try {
                const pedido = await llamarApi(`/pedidos/${pedidoId}/enviar`, "POST");
                pintarResultado(pedido);
                await cargarPedidos();
            } catch (err) {
                pintarResultado({ error: err.message });
            }
        });
    });

    // 3. Cancelar y eliminar pedido pendiente
    document.querySelectorAll(".btn-accion-eliminar").forEach((btn) => {
        btn.addEventListener("click", async () => {
            const pedidoId = btn.dataset.id;
            const confirmar = confirm(`¿Estás seguro de cancelar y eliminar el pedido #${pedidoId}? El inventario será devuelto.`);
            if (!confirmar) return;

            try {
                const res = await llamarApi(`/pedidos/${pedidoId}`, "DELETE");
                const el = document.getElementById("resultado");
                el.innerHTML = `
                    <div style="background: rgba(16, 185, 129, 0.15); border: 1px solid #10b981; color: #6ee7b7; padding: 12px; border-radius: 8px;">
                        <strong>✓ Éxito:</strong> ${res.mensaje || `Pedido #${pedidoId} eliminado con éxito.`}
                    </div>
                `;
                // Si los campos de pago o despacho tenían este ID, limpiarlos
                if (document.getElementById("pedido_id_pago").value == pedidoId) {
                    document.getElementById("pedido_id_pago").value = "";
                }
                if (document.getElementById("pedido_id_enviar").value == pedidoId) {
                    document.getElementById("pedido_id_enviar").value = "";
                }
                await cargarPedidos();
            } catch (err) {
                pintarResultado({ error: err.message });
            }
        });
    });
}

// Cargar pedidos desde la API
async function cargarPedidos() {
    try {
        pedidosMemoria = await llamarApi("/pedidos");
        renderizarTabla();
    } catch (err) {
        console.error("Error al cargar pedidos:", err);
    }
}

// Configurar los botones de filtrado rápido
document.querySelectorAll(".btn-filtro").forEach((btn) => {
    btn.addEventListener("click", (e) => {
        document.querySelectorAll(".btn-filtro").forEach(b => b.style.opacity = "0.7");
        e.target.style.opacity = "1";
        filtroActual = e.target.dataset.filtro;
        renderizarTabla();
    });
});

document.getElementById("btn-refrescar").addEventListener("click", cargarPedidos);

// Carga inicial
cargarPedidos();