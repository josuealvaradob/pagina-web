"""
domain_state.py — Patrón State

CASO MALO (estaba en app/main.py): el estado del pedido era un string
libre (pedido["estado"] = "enviado"). Nada impedía marcar un pedido como
enviado sin haber sido pagado antes — el bug que documentamos en el
diagnóstico inicial.

CASO BUENO (este archivo): cada estado es una clase que solo sabe a qué
estados puede transicionar. El pedido delega ahí la validación, en vez de
mutar el string directamente.
"""

from __future__ import annotations

import abc


class EstadoInvalidoError(Exception):
    """Se lanza cuando se intenta una transición de estado no permitida."""


class EstadoPedido(abc.ABC):
    nombre: str

    @abc.abstractmethod
    def pagar(self, pedido: dict) -> None: ...

    @abc.abstractmethod
    def enviar(self, pedido: dict) -> None: ...

    @abc.abstractmethod
    def cancelar(self, pedido: dict) -> None: ...


class EstadoPendiente(EstadoPedido):
    nombre = "pendiente"

    def pagar(self, pedido: dict) -> None:
        pedido["estado"] = EstadoPagado.nombre

    def enviar(self, pedido: dict) -> None:
        raise EstadoInvalidoError("No se puede enviar un pedido que no ha sido pagado")

    def cancelar(self, pedido: dict) -> None:
        pedido["estado"] = EstadoCancelado.nombre


class EstadoPagado(EstadoPedido):
    nombre = "pagado"

    def pagar(self, pedido: dict) -> None:
        raise EstadoInvalidoError("El pedido ya fue pagado")

    def enviar(self, pedido: dict) -> None:
        pedido["estado"] = EstadoEnviado.nombre

    def cancelar(self, pedido: dict) -> None:
        pedido["estado"] = EstadoCancelado.nombre


class EstadoEnviado(EstadoPedido):
    nombre = "enviado"

    def pagar(self, pedido: dict) -> None:
        raise EstadoInvalidoError(
            "El pedido ya fue enviado, no se puede pagar de nuevo"
        )

    def enviar(self, pedido: dict) -> None:
        raise EstadoInvalidoError("El pedido ya fue enviado")

    def cancelar(self, pedido: dict) -> None:
        raise EstadoInvalidoError("No se puede cancelar un pedido ya enviado")


class EstadoCancelado(EstadoPedido):
    nombre = "cancelado"

    def pagar(self, pedido: dict) -> None:
        raise EstadoInvalidoError("No se puede pagar un pedido cancelado")

    def enviar(self, pedido: dict) -> None:
        raise EstadoInvalidoError("No se puede enviar un pedido cancelado")

    def cancelar(self, pedido: dict) -> None:
        raise EstadoInvalidoError("El pedido ya está cancelado")


_ESTADOS: dict[str, EstadoPedido] = {
    "pendiente": EstadoPendiente(),
    "pagado": EstadoPagado(),
    "enviado": EstadoEnviado(),
    "cancelado": EstadoCancelado(),
}


def obtener_estado(nombre_estado: str) -> EstadoPedido:
    return _ESTADOS[nombre_estado]
