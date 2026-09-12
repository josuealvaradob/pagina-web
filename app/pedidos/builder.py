"""
builder.py — Patrón Builder

CASO MALO (estaba en app/main.py, endpoint crear_pedido): la construcción
del pedido (subtotal, descuentos, empaque, envío) se hacía en un único
bloque secuencial dentro del endpoint HTTP. Cualquier paso nuevo (ej.
impuestos) obligaba a reescribir ese bloque completo.

CASO BUENO (este archivo): PedidoBuilder arma el pedido paso a paso,
delegando el cálculo del precio a la cadena de Decorator y el costo de
envío a la Strategy correspondiente. El endpoint ya no conoce los
detalles de cómo se calcula cada cosa, solo pide "constrúyeme el pedido".
"""

from __future__ import annotations

from app.pedidos import decorator
from app.envios import strategy


class PedidoBuilder:
    def __init__(self) -> None:
        self._cliente: str | None = None
        self._items: list[dict] = []
        self._cupon: str | None = None
        self._empaque_regalo: bool = False
        self._estrategia_envio: strategy.EstrategiaEnvio | None = None
        self._tipo_envio: str | None = None

    def para_cliente(self, cliente: str) -> "PedidoBuilder":
        self._cliente = cliente
        return self

    def con_items(self, items: list[dict]) -> "PedidoBuilder":
        self._items = items
        return self

    def con_cupon(self, cupon: str | None) -> "PedidoBuilder":
        self._cupon = cupon
        return self

    def con_empaque_regalo(self, activo: bool) -> "PedidoBuilder":
        self._empaque_regalo = activo
        return self

    def con_estrategia_envio(
        self, estrategia: strategy.EstrategiaEnvio, tipo_envio: str
    ) -> "PedidoBuilder":
        self._estrategia_envio = estrategia
        self._tipo_envio = tipo_envio
        return self

    def build(self) -> dict:
        if not self._cliente:
            raise ValueError("El pedido requiere un cliente")
        if not self._items:
            raise ValueError("El pedido requiere al menos un item")
        if self._estrategia_envio is None:
            raise ValueError("El pedido requiere una estrategia de envío")

        subtotal = sum(
            item["cantidad"] * item["precio_unitario"] for item in self._items
        )

        componente_precio = decorator.PrecioBase(subtotal)
        if self._cupon:
            componente_precio = decorator.CuponDescuento(componente_precio, self._cupon)
        if self._empaque_regalo:
            componente_precio = decorator.EmpaqueRegalo(componente_precio)

        total_con_extras = componente_precio.calcular()
        costo_empaque = 5000 if self._empaque_regalo else 0
        descuento = subtotal - (total_con_extras - costo_empaque)

        costo_envio = self._estrategia_envio.calcular_costo(total_con_extras)
        total_final = total_con_extras + costo_envio

        return {
            "cliente": self._cliente,
            "items": self._items,
            "cupon": self._cupon,
            "tipo_envio": self._tipo_envio,
            "subtotal": subtotal,
            "descuento": round(descuento, 2),
            "costo_empaque": costo_empaque,
            "costo_envio": costo_envio,
            "total": round(total_final, 2),
            "estado": "pendiente",
            "metodo_pago": None,
        }
