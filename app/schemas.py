import pydantic


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
    telefono_nequi: str | None = None
