import fastapi
from app import database, schemas, domain_state
from app.envios import strategy
from app.pedidos import builder
from datetime import datetime

router = fastapi.APIRouter()


@router.post("/")
def crear_pedido(req: schemas.CrearPedidoRequest):
    items = [i.model_dump() for i in req.items]

    for item in items:
        if item["producto"] not in database.INVENTARIO:
            raise fastapi.HTTPException(400, f"Producto {item['producto']} no existe")
        if database.INVENTARIO[item["producto"]] < item["cantidad"]:
            raise fastapi.HTTPException(400, f"Sin stock de {item['producto']}")

    try:
        estrategia_envio = strategy.obtener_estrategia_envio(req.tipo_envio)
        pedido_data = (
            builder.PedidoBuilder()
            .para_cliente(req.cliente)
            .con_items(items)
            .con_cupon(req.cupon)
            .con_empaque_regalo(req.empaque_regalo)
            .con_estrategia_envio(estrategia_envio, req.tipo_envio)
            .build()
        )
    except ValueError as exc:
        raise fastapi.HTTPException(status_code=400, detail=str(exc))

    for item in items:
        database.INVENTARIO[item["producto"]] -= item["cantidad"]

    database.CONTADOR_PEDIDOS += 1
    pedido_data["id"] = database.CONTADOR_PEDIDOS
    pedido_data["fecha"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    database.PEDIDOS[database.CONTADOR_PEDIDOS] = pedido_data

    return pedido_data


@router.delete("/{pedido_id}")
def eliminar_pedido(pedido_id: int):
    if pedido_id not in database.PEDIDOS:
        raise fastapi.HTTPException(404, f"Pedido #{pedido_id} no encontrado")

    pedido = database.PEDIDOS[pedido_id]
    if pedido.get("estado") != "pendiente":
        raise fastapi.HTTPException(
            400, f"No se puede eliminar el pedido en estado '{pedido.get('estado')}'."
        )

    for item in pedido.get("items", []):
        prod = item.get("producto")
        if prod in database.INVENTARIO:
            database.INVENTARIO[prod] += item.get("cantidad", 0)

    del database.PEDIDOS[pedido_id]
    return {
        "mensaje": f"Pedido #{pedido_id} cancelado y eliminado correctamente. Stock restituido."
    }


@router.get("/{pedido_id}")
def obtener_pedido(pedido_id: int):
    if pedido_id not in database.PEDIDOS:
        raise fastapi.HTTPException(404, "Pedido no encontrado")
    return database.PEDIDOS[pedido_id]


@router.get("/")
def listar_pedidos():
    return list(database.PEDIDOS.values())


@router.post("/{pedido_id}/enviar")
def marcar_enviado(pedido_id: int):
    if pedido_id not in database.PEDIDOS:
        raise fastapi.HTTPException(404, "Pedido no encontrado")

    pedido = database.PEDIDOS[pedido_id]
    try:
        estado_actual = domain_state.obtener_estado(pedido["estado"])
        estado_actual.enviar(pedido)
    except domain_state.EstadoInvalidoError as exc:
        raise fastapi.HTTPException(400, str(exc))

    return pedido
