import fastapi
from app import database, schemas, domain_state
from app.pagos import factory, observer

router = fastapi.APIRouter()


@router.post("/")
def procesar_pago(req: schemas.PagoRequest):
    if req.pedido_id not in database.PEDIDOS:
        raise fastapi.HTTPException(404, "Pedido no encontrado")

    pedido = database.PEDIDOS[req.pedido_id]
    if pedido["estado"] != "pendiente":
        raise fastapi.HTTPException(400, "El pedido ya fue procesado")

    try:
        metodo_pago = factory.crear_metodo_pago(req.metodo_pago)
        metodo_pago.validar_credenciales(req.model_dump())
        metodo_pago.cobrar(pedido["total"], req.model_dump())

        estado_actual = domain_state.obtener_estado(pedido["estado"])
        estado_actual.pagar(pedido)
    except (factory.ErrorPago, domain_state.EstadoInvalidoError) as exc:
        raise fastapi.HTTPException(400, str(exc))

    pedido["metodo_pago"] = req.metodo_pago
    sujeto_pago = observer.crear_sujeto_pago_default()
    sujeto_pago.notificar(pedido)

    return pedido
