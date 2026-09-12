"""
observer.py — Patrón Observer

CASO MALO (estaba en app/main.py, endpoint procesar_pago): el endpoint
llamaba directo a print() de "email", "inventario" y "logística", uno
abajo del otro. Agregar un canal nuevo (ej. Slack, SMS) implicaba volver
a editar ese mismo endpoint.

CASO BUENO (este archivo): SujetoPago mantiene una lista de observadores
y los notifica sin conocer sus implementaciones. Agregar un canal nuevo
es una clase nueva + una línea de suscripción, sin tocar el endpoint.
"""

from __future__ import annotations

import abc


class ObservadorPedido(abc.ABC):
    @abc.abstractmethod
    def actualizar(self, pedido: dict) -> None: ...


class NotificadorEmail(ObservadorPedido):
    def actualizar(self, pedido: dict) -> None:
        print(f"[EMAIL] Confirmación de pago enviada a {pedido['cliente']}")


class ActualizadorInventario(ObservadorPedido):
    def actualizar(self, pedido: dict) -> None:
        print(f"[INVENTARIO] Confirmando salida de stock del pedido {pedido['id']}")


class NotificadorLogistica(ObservadorPedido):
    def actualizar(self, pedido: dict) -> None:
        if pedido["costo_envio"] > 0:
            print(f"[LOGISTICA] Pedido {pedido['id']} listo para despacho")


class SujetoPago:
    def __init__(self) -> None:
        self._observadores: list[ObservadorPedido] = []

    def suscribir(self, observador: ObservadorPedido) -> None:
        self._observadores.append(observador)

    def notificar(self, pedido: dict) -> None:
        for observador in self._observadores:
            observador.actualizar(pedido)


def crear_sujeto_pago_default() -> SujetoPago:
    """Fábrica de conveniencia con los observadores estándar del sistema."""
    sujeto = SujetoPago()
    sujeto.suscribir(NotificadorEmail())
    sujeto.suscribir(ActualizadorInventario())
    sujeto.suscribir(NotificadorLogistica())
    return sujeto
