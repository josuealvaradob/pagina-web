const API_BASE = "/api";

// ---------------------------------------------------------------------
// Utilidades
// ---------------------------------------------------------------------
function pintarResultado(obj) {
    const el = document.getElementById("resultado");
    el.textContent = JSON.stringify(obj, null, 2);
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
document.getElementById("btn-add-item").addEventListener("click", () => {
    const container = document.getElementById("items-container");
    const row = document.createElement("div");
    row.className = "item-row";
    row.innerHTML = `
        <select class="item-producto">
            <option value="perfume_hombre">Perfume Hombre 100ml</option>
            <option value="perfume_mujer">Perfume Mujer 100ml</option>
            <option value="mini_perfume">Mini Perfume 30ml</option>
        </select>
        <input type="number" class="item-cantidad" min="1" value="1" placeholder="Cantidad">
        <input type="number" class="item-precio" min="1" value="120000" placeholder="Precio unitario">
        <button type="button" class="btn-remove-item" title="Quitar">✕</button>
    `;
    row.querySelector(".btn-remove-item").addEventListener("click", () => row.remove());
    container.appendChild(row);
});

document.querySelectorAll(".btn-remove-item").forEach((btn) => {
    btn.addEventListener("click", (e) => e.target.closest(".item-row").remove());
});

// ---------------------------------------------------------------------
// Crear pedido
// ---------------------------------------------------------------------
document.getElementById("form-pedido").addEventListener("submit", async (e) => {
    e.preventDefault();

    const items = Array.from(document.querySelectorAll(".item-row")).map((row) => ({
        producto: row.querySelector(".item-producto").value,
        cantidad: parseInt(row.querySelector(".item-cantidad").value, 10),
        precio_unitario: parseFloat(row.querySelector(".item-precio").value),
    }));

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
        cargarPedidos();
    } catch (err) {
        pintarResultado({ error: err.message });
    }
});

// ---------------------------------------------------------------------
// Campos dinámicos según método de pago
// ---------------------------------------------------------------------
const CAMPOS_POR_METODO = {
    tarjeta: [{ id: "token_tarjeta", label: "Token de tarjeta", value: "tok_visa_123" }],
    paypal: [{ id: "email_paypal", label: "Email de PayPal", value: "cliente@correo.com" }],
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
// Procesar pago
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
        cargarPedidos();
    } catch (err) {
        pintarResultado({ error: err.message });
    }
});

// ---------------------------------------------------------------------
// Marcar como enviado
// ---------------------------------------------------------------------
document.getElementById("form-enviar").addEventListener("submit", async (e) => {
    e.preventDefault();
    const id = document.getElementById("pedido_id_enviar").value;
    try {
        const pedido = await llamarApi(`/pedidos/${id}/enviar`, "POST");
        pintarResultado(pedido);
        cargarPedidos();
    } catch (err) {
        pintarResultado({ error: err.message });
    }
});

// ---------------------------------------------------------------------
// Listado de pedidos
// ---------------------------------------------------------------------
async function cargarPedidos() {
    try {
        const pedidos = await llamarApi("/pedidos");
        const contenedor = document.getElementById("lista-pedidos");
        contenedor.innerHTML = "";
        pedidos.forEach((p) => {
            const div = document.createElement("div");
            div.className = "pedido-item";
            div.innerHTML = `
                <span>#${p.id} — ${p.cliente} — $${p.total.toLocaleString("es-CO")}</span>
                <span class="badge ${p.estado}">${p.estado}</span>
            `;
            contenedor.appendChild(div);
        });
    } catch (err) {
        console.error(err);
    }
}

document.getElementById("btn-refrescar").addEventListener("click", cargarPedidos);
cargarPedidos();