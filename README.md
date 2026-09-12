# pagina-web
Proyecto final del curso Diseño Orientado a Objetos y Patrones - Sistema de Gestión de Órdenes de Trabajo y Mantenimiento.
# Los Samarios del Perfume — API de E-commerce con Patrones de Diseño GoF

## Descripción general

El sistema simula el backend de una tienda de perfumes que permite:

- Crear pedidos con múltiples productos (marca + tamaño), aplicando cupones
  de descuento (con monto mínimo de compra) y empaque de regalo opcional.
- Calcular el costo de envío según el tipo elegido (estándar, exprés, gratis),
  con reglas de negocio propias para cada uno.
- Procesar el pago con distintos métodos (tarjeta, Nequi), cada uno con sus
  propias reglas de validación.
- Controlar el ciclo de vida del pedido (pendiente → pagado → enviado, o
  cancelado), evitando transiciones inválidas.
- Notificar automáticamente a distintos "canales" (email, inventario,
  logística) cuando se confirma un pago.
- Administrar el inventario y los pedidos desde un panel web interactivo,
  con filtros por estado.
- Exportar el historial completo de pedidos a un archivo Excel (`.xlsx`).

El objetivo académico del proyecto es demostrar, con un caso de uso real,
cómo la aplicación de patrones de diseño y una arquitectura organizada por
routers mejora la mantenibilidad, extensibilidad y calidad de un sistema que
originalmente estaba escrito como un monolito con lógica de negocio mezclada
directamente en los endpoints HTTP.

---
## Diagnóstico: el problema en la versión "antes"

Antes de aplicar los patrones, toda la lógica vivía en un único archivo
(`main.py`), con los endpoints haciendo todo el trabajo directamente:

| Problema detectado | Ubicación original | Consecuencia |
|---|---|---|
| `if/elif` anidados para calcular descuentos por cupón | `crear_pedido` | Agregar un cupón nuevo obligaba a editar el endpoint |
| `+= 5000` hardcodeado para el empaque de regalo | `crear_pedido` | El costo de empaque no era reutilizable ni combinable de forma ordenada |
| `if/elif` anidados para el costo de envío | `crear_pedido` | Las reglas de negocio (envío gratis sobre cierto monto) estaban mezcladas con el cálculo mismo |
| `if/elif` anidados para validar credenciales de pago | `procesar_pago` | Agregar un método de pago nuevo obligaba a editar el endpoint existente |
| Estado del pedido como *string* libre (`pedido["estado"] = "enviado"`) | `marcar_enviado` | **Bug real**: no existía ninguna validación que impidiera marcar un pedido como enviado sin haber sido pagado antes |
| `print()` de email/inventario/logística pegados directamente al flujo de pago | `procesar_pago` | Agregar un canal de notificación nuevo obligaba a editar el endpoint |
| Construcción del pedido (subtotal, descuento, empaque, envío) en un único bloque secuencial | `crear_pedido` (función completa) | Sin ningún punto claro de orquestación; toda la lógica de armado vivía mezclada con la validación HTTP |
| Toda la aplicación en un solo archivo `main.py` | Proyecto completo | Baja cohesión: crecer el proyecto implicaba seguir agregando código al mismo archivo |

Cada uno de estos problemas se resolvió aplicando el patrón de diseño GoF
correspondiente, listados a continuación, además de reorganizar los
endpoints en routers separados por dominio (`pedidos`, `pagos`).

---
