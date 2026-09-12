"""
decorator.py — Patrón Decorator
CASO MALO (estaba en app/main.py, endpoint crear_pedido): los descuentos
por cupón eran un if/elif anidado, y el empaque de regalo era un
"+= 5000" hardcodeado justo después. Agregar un cupón nuevo, o combinar
cupón + empaque + un futuro "seguro de envío", significaba seguir
apilando condicionales en el mismo bloque.

CASO BUENO (este archivo): el precio base se envuelve en capas sucesivas
(cupón, empaque). Cada envoltura no sabe de la existencia de la otra —
agregar un descuento nuevo es una clase nueva, no una rama más en un
if/elif existente.
"""

from __future__ import annotations

import abc


class ComponentePrecio(abc.ABC):
    @abc.abstractmethod
    def calcular(self) -> float: ...


class PrecioBase(ComponentePrecio):
    def __init__(self, subtotal: float) -> None:
        self._subtotal = subtotal

    def calcular(self) -> float:
        return self._subtotal


class DecoradorPrecio(ComponentePrecio):
    def __init__(self, envuelto: ComponentePrecio) -> None:
        self._envuelto = envuelto

    @abc.abstractmethod
    def calcular(self) -> float: ...


class CuponDescuento(DecoradorPrecio):
    # Definimos (monto_minimo, porcentaje)
    _REGLAS = {
        "DESC10": (120_000, 0.10),
        "DESC20": (200_000, 0.20),
        "BLACKFRIDAY": (200_000, 0.30),
    }

    def __init__(self, envuelto: ComponentePrecio, codigo_cupon: str) -> None:
        super().__init__(envuelto)
        self._codigo = codigo_cupon

    def calcular(self) -> float:
        monto_previo = self._envuelto.calcular()
        regla = self._REGLAS.get(self._codigo)

        if regla is None:
            return monto_previo

        monto_minimo, porcentaje = regla
        if monto_previo <= monto_minimo:
            raise ValueError(
                f"No se puede procesar el pedido con el cupón {self._codigo}: "
                f"el valor de los productos no alcanza el mínimo de ${monto_minimo:,.0f}. "
                f"Por favor incrementa la compra o selecciona 'Ninguno' en la opción de cupón."
            )

        return monto_previo - (monto_previo * porcentaje)


class EmpaqueRegalo(DecoradorPrecio):
    COSTO_FIJO = 5000

    def calcular(self) -> float:
        return self._envuelto.calcular() + self.COSTO_FIJO
