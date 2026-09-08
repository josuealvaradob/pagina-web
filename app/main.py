"""
main.py — VERSIÓN "ANTES"sin patrones.
"""

from pathlib import Path

import fastapi
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import pydantic

BASE_DIR = Path(__file__).resolve().parent.parent

app = fastapi.FastAPI(title="Tienda Online (ANTES)")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# --- "Base de datos" en memoria, variables globales mutables ---
PEDIDOS = {}
INVENTARIO = {"perfume_hombre": 40, "perfume_mujer": 40, "mini_perfume": 60}
CONTADOR_PEDIDOS = 0


class ItemPedido(pydantic.BaseModel):
    producto: str
    cantidad: int
    precio_unitario: float


class CrearPedidoRequest(pydantic.BaseModel):
    cliente: str
    items: list[ItemPedido]
    tipo_envio: str
    cupon: str | None = None
    empaque_regalo: bool = False


class PagoRequest(pydantic.BaseModel):
    pedido_id: int
    metodo_pago: str
    token_tarjeta: str | None = None
    email_paypal: str | None = None
    telefono_nequi: str | None = None


@app.get("/")
def index(request: fastapi.Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/pedidos")
# comeinza el build de la funcion crear pedido
def crear_pedido(req: CrearPedidoRequest):
    global CONTADOR_PEDIDOS

    for item in req.items:
        if item.producto not in INVENTARIO:
            raise fastapi.HTTPException(400, f"Producto {item.producto} no existe")
        if INVENTARIO[item.producto] < item.cantidad:
            raise fastapi.HTTPException(400, f"Sin stock de {item.producto}")

    subtotal = sum(i.precio_unitario * i.cantidad for i in req.items)

    # --- if/elif anidados para el cupón (PROBLEMA: solucion Decorator) ---
    descuento = 0.0
    if req.cupon == "DESC10":
        descuento = subtotal * 0.10
    elif req.cupon == "DESC20":
        descuento = subtotal * 0.20 if subtotal > 100000 else subtotal * 0.05
    elif req.cupon == "BLACKFRIDAY":
        if subtotal > 200000:
            descuento = subtotal * 0.30
        elif subtotal > 100000:
            descuento = subtotal * 0.15

    total = subtotal - descuento

    # --- empaque hardcodeado (PROBLEMA: solucion Decorator) ---
    costo_empaque = 5000 if req.empaque_regalo else 0
    total += costo_empaque

    # --- if/elif anidados para envío (PROBLEMA: solucion Strategy) ---
    if req.tipo_envio == "estandar":
        costo_envio = 0 if total > 150000 else 8000
    elif req.tipo_envio == "expres":
        costo_envio = 5000 if total > 150000 else 15000
    elif req.tipo_envio == "gratis":
        costo_envio = 0
    else:
        raise fastapi.HTTPException(400, "Tipo de envío inválido")

    total += costo_envio

    for item in req.items:
        INVENTARIO[item.producto] -= item.cantidad

    CONTADOR_PEDIDOS += 1
    pedido_id = CONTADOR_PEDIDOS

    # estado como string libre (PROBLEMA: solucion State)
    PEDIDOS[pedido_id] = {
        "id": pedido_id,
        "cliente": req.cliente,
        "items": [i.model_dump() for i in req.items],
        "subtotal": subtotal,
        "descuento": descuento,
        "costo_empaque": costo_empaque,
        "costo_envio": costo_envio,
        "total": total,
        "estado": "pendiente",
        "metodo_pago": None,
    }
    return PEDIDOS[pedido_id]


@app.post("/api/pagos")
def procesar_pago(req: PagoRequest):
    if req.pedido_id not in PEDIDOS:
        raise fastapi.HTTPException(404, "Pedido no encontrado")
    pedido = PEDIDOS[req.pedido_id]
    if pedido["estado"] != "pendiente":
        raise fastapi.HTTPException(400, "El pedido ya fue procesado")

    # --- if/elif anidados por pasarela (PROBLEMA: solucion Factory Method) ---
    if req.metodo_pago == "tarjeta":
        if not req.token_tarjeta:
            raise fastapi.HTTPException(400, "Falta token de tarjeta")
        print(f"Cobrando {pedido['total']} con tarjeta {req.token_tarjeta}")
    elif req.metodo_pago == "paypal":
        if not req.email_paypal:
            raise fastapi.HTTPException(400, "Falta email de PayPal")
        print(f"Cobrando {pedido['total']} con PayPal {req.email_paypal}")
    elif req.metodo_pago == "nequi":
        if not req.telefono_nequi:
            raise fastapi.HTTPException(400, "Falta teléfono de Nequi")
        print(f"Cobrando {pedido['total']} con Nequi {req.telefono_nequi}")
    else:
        raise fastapi.HTTPException(400, "Método de pago no soportado")

    pedido["estado"] = "pagado"
    pedido["metodo_pago"] = req.metodo_pago

    # --- efectos secundarios acoplados (PROBLEMA: solucion Observer) ---
    print(f"[EMAIL] Confirmación de pago enviada a {pedido['cliente']}")
    print(f"[INVENTARIO] Confirmando salida de stock del pedido {pedido['id']}")
    if pedido["costo_envio"] > 0 and req.metodo_pago:
        print(f"[LOGISTICA] Pedido {pedido['id']} listo para despacho")

    return pedido


@app.post("/api/pedidos/{pedido_id}/enviar")
def marcar_enviado(pedido_id: int):
    if pedido_id not in PEDIDOS:
        raise fastapi.HTTPException(404, "Pedido no encontrado")
    pedido = PEDIDOS[pedido_id]
    # BUG a propósito: nada valida que ya haya sido pagado
    pedido["estado"] = "enviado"
    return pedido


@app.get("/api/pedidos/{pedido_id}")
def obtener_pedido(pedido_id: int):
    if pedido_id not in PEDIDOS:
        raise fastapi.HTTPException(404, "Pedido no encontrado")
    return PEDIDOS[pedido_id]


@app.get("/api/pedidos")
def listar_pedidos():
    return list(PEDIDOS.values())


@app.get("/api/inventario")
def ver_inventario():
    return INVENTARIO
