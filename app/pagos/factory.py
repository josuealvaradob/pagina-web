"""
factory.py — Patrón Factory Method

CASO MALO (estaba en app/main.py, endpoint procesar_pago): un if/elif/else
validaba credenciales y "cobraba" según el método de pago, todo dentro del
mismo endpoint HTTP.

CASO BUENO (este archivo): cada método de pago es una clase con la misma
interfaz (MetodoPago). crear_metodo_pago decide cuál instanciar según el
texto recibido — el endpoint ya no conoce las diferencias entre tarjeta,
PayPal o Nequi.
"""

from __future__ import annotations

import abc


class ErrorPago(Exception):
    """Error de negocio al procesar un pago."""


class MetodoPago(abc.ABC):
    @abc.abstractmethod
    def validar_credenciales(self, datos: dict) -> None: ...

    @abc.abstractmethod
    def cobrar(self, monto: float, datos: dict) -> str: ...


class MetodoTarjeta(MetodoPago):
    def validar_credenciales(self, datos: dict) -> None:
        if not datos.get("token_tarjeta"):
            raise ErrorPago("Falta token de tarjeta")

    def cobrar(self, monto: float, datos: dict) -> str:
        token = datos["token_tarjeta"]
        return f"Cobrando {monto} con tarjeta {token}"


class MetodoNequi(MetodoPago):
    def validar_credenciales(self, datos: dict) -> None:
        if not datos.get("telefono_nequi"):
            raise ErrorPago("Falta teléfono de Nequi")

    def cobrar(self, monto: float, datos: dict) -> str:
        telefono = datos["telefono_nequi"]
        return f"Cobrando {monto} con Nequi {telefono}"


_REGISTRO_METODOS: dict[str, type[MetodoPago]] = {
    "tarjeta": MetodoTarjeta,
    "nequi": MetodoNequi,
}


def crear_metodo_pago(metodo_pago: str) -> MetodoPago:
    """Factory Method: dado un método de pago, devuelve la instancia
    concreta correcta sin que el llamador conozca las clases."""
    clase = _REGISTRO_METODOS.get(metodo_pago)
    if clase is None:
        raise ErrorPago(f"Método de pago no soportado: {metodo_pago}")
    return clase()
