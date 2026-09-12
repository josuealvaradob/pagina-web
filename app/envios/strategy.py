"""
strategy.py — Patrón Strategy
CASO MALO (estaba en app/main.py, endpoint crear_pedido): el costo de
envío era un if/elif/else con reglas de negocio (envío gratis sobre
cierto monto) mezcladas con el propio cálculo, dentro del endpoint.

CASO BUENO (este archivo): cada tipo de envío es una clase con la misma
interfaz (calcular_costo). Agregar un tipo de envío nuevo es una clase
nueva, sin tocar las existentes ni el endpoint.
"""

from __future__ import annotations

import abc


class EstrategiaEnvio(abc.ABC):
    @abc.abstractmethod
    def calcular_costo(self, total_pedido: float) -> float: ...


class EnvioEstandar(EstrategiaEnvio):
    UMBRAL_GRATIS = 150_000
    COSTO_BASE = 8_000

    def calcular_costo(self, total_pedido: float) -> float:
        return 0.0 if total_pedido > self.UMBRAL_GRATIS else self.COSTO_BASE


class EnvioExpres(EstrategiaEnvio):
    UMBRAL_DESCUENTO = 150_000
    COSTO_NORMAL = 15_000
    COSTO_CON_DESCUENTO = 5_000

    def calcular_costo(self, total_pedido: float) -> float:
        return (
            self.COSTO_CON_DESCUENTO
            if total_pedido > self.UMBRAL_DESCUENTO
            else self.COSTO_NORMAL
        )


class EnvioGratis(EstrategiaEnvio):
    MONTO_MINIMO = 200_000

    def calcular_costo(self, total_pedido: float) -> float:
        if total_pedido < self.MONTO_MINIMO:
            raise ValueError(
                f"El envío gratis solo aplica para compras superiores a ${self.MONTO_MINIMO:,.0f}"
            )
        return 0.0


_ESTRATEGIAS: dict[str, type[EstrategiaEnvio]] = {
    "estandar": EnvioEstandar,
    "expres": EnvioExpres,
    "gratis": EnvioGratis,
}


def obtener_estrategia_envio(tipo_envio: str) -> EstrategiaEnvio:
    clase = _ESTRATEGIAS.get(tipo_envio)
    if clase is None:
        raise ValueError(f"Tipo de envío inválido: {tipo_envio}")
    return clase()
