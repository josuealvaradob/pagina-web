# pagina-web
Proyecto final del curso Diseño Orientado a Objetos y Patrones - Sistema de Gestión de Órdenes de Trabajo y Mantenimiento.
# Los Samarios del Perfume — API de E-commerce con Patrones de Diseño GoF

Proyecto académico — Actividad 4: Proyecto integrador.
API de e-commerce para una perfumería, construida con **FastAPI**, refactorizada
desde un monolito sin patrones de diseño hacia una arquitectura organizada por
routers, con **6 patrones de diseño GoF** (Gang of Four).

---



---

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

## Estructura del proyecto

```
pagina-web/
├── requirements.txt
├── README.md
├── .gitignore
├── app/
│   ├── main.py                 # Arranque de FastAPI, monta routers y estáticos
│   ├── database.py             # "Base de datos" en memoria (inventario, pedidos)
│   ├── schemas.py              # DTOs Pydantic compartidos
│   ├── domain_state.py         # Patrón State
│   ├── pedidos/
│   │   ├── router.py           # Endpoints de creación, envío y eliminación
│   │   ├── builder.py          # Patrón Builder
│   │   └── decorator.py        # Patrón Decorator
│   ├── pagos/
│   │   ├── router.py           # Endpoint de procesamiento de pago
│   │   ├── factory.py          # Patrón Factory Method
│   │   └── observer.py         # Patrón Observer
│   └── envios/
│       └── strategy.py         # Patrón Strategy
├── static/
│   ├── css/style.css
│   ├── js/app.js
│   └── img/logo.jpeg
└── templates/
    └── index.html              # Panel administrativo
```

> **Nota técnica:** el proyecto no usa archivos `__init__.py` en las
> subcarpetas de `app/`. Esto es válido porque Python 3.3+ soporta *paquetes
> de espacio de nombres implícitos*, que no requieren ese archivo para que
> los imports (`from app.pedidos import builder`) funcionen correctamente.

---

## Instalación y ejecución

### 1. Crear y activar entorno virtual

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / Mac
source .venv/bin/activate
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Ejecutar el servidor

```bash
uvicorn app.main:app --reload --port 8000
```

### 4. Abrir en el navegador

- **Panel administrativo:** http://127.0.0.1:8000/
- **Documentación interactiva (Swagger):** http://127.0.0.1:8000/docs

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

## Los 6 patrones de diseño aplicados

### 1. Factory Method — `app/pagos/factory.py`

**Problema que resuelve:** el `if/elif/else` que validaba credenciales y
"cobraba" según el método de pago, todo dentro del mismo endpoint.

**Solución:** cada método de pago (`MetodoTarjeta`, `MetodoNequi`) es una
clase que implementa la interfaz `MetodoPago`. La función `crear_metodo_pago`
decide qué clase instanciar según el texto recibido, sin que el router
conozca las clases concretas.

**Por qué este patrón:** varias implementaciones que comparten la misma
interfaz, seleccionadas en tiempo de ejecución según un identificador.
Permite agregar un método de pago nuevo sin modificar código existente
(Open/Closed Principle).

### 2. Strategy — `app/envios/strategy.py`

**Problema que resuelve:** el costo de envío calculado con `if/elif/else`,
con reglas de negocio (envío gratis sobre cierto monto) mezcladas con el
cálculo mismo.

**Solución:** cada tipo de envío (`EnvioEstandar`, `EnvioExpres`,
`EnvioGratis`) es una clase con la interfaz `EstrategiaEnvio.calcular_costo`.
`EnvioGratis` valida además un monto mínimo de compra, lanzando `ValueError`
si no se cumple.

**Por qué este patrón:** el tipo de envío es un algoritmo intercambiable en
tiempo de ejecución. Se prefirió sobre un diccionario de funciones porque
cada estrategia encapsula sus propias constantes de configuración sin
romper el contrato común.

### 3. Decorator — `app/pedidos/decorator.py`

**Problema que resuelve:** descuentos por cupón e incremento por empaque de
regalo, aplicados con `if/elif` y un `+=` hardcodeado en el mismo bloque.

**Solución:** el precio base (`PrecioBase`) se envuelve en capas sucesivas
(`CuponDescuento`, `EmpaqueRegalo`). `CuponDescuento` valida un monto mínimo
de compra por cupón (`DESC10`, `DESC20`, `BLACKFRIDAY`), rechazando el
pedido con `ValueError` si no se alcanza.

**Por qué este patrón y no Strategy:** cupón y empaque son efectos
**independientes y combinables** (se pueden aplicar ambos a la vez), a
diferencia del tipo de envío, que es una elección **excluyente**. Decorator
compone efectos acumulables sin que cada uno conozca a los demás.

### 4. State — `app/domain_state.py`

**Problema que resuelve:** el bug real del proyecto — el estado del pedido
era un *string* libre, sin ninguna validación de transición.

**Solución:** cada estado (`EstadoPendiente`, `EstadoPagado`,
`EstadoEnviado`, `EstadoCancelado`) es una clase que implementa `pagar()`,
`enviar()` y `cancelar()`, decidiendo por sí misma si la transición es
válida o lanza `EstadoInvalidoError`.

**Por qué este patrón:** concentra todas las reglas de transición de un
estado en una sola clase, en vez de repartir validaciones `if` por
distintos endpoints. Agregar un estado nuevo es una clase adicional, sin
modificar las existentes.

### 5. Observer — `app/pagos/observer.py`

**Problema que resuelve:** los `print()` de notificación (email, inventario,
logística) llamados directamente, uno tras otro, dentro del endpoint de
pago.

**Solución:** `SujetoPago` mantiene una lista de observadores
(`NotificadorEmail`, `ActualizadorInventario`, `NotificadorLogistica`) y los
notifica sin conocer sus implementaciones concretas.

**Por qué este patrón:** desacopla al que genera el evento ("pago
confirmado") de quienes reaccionan a él. Agregar un canal nuevo es una
clase adicional suscrita al sujeto, sin tocar el endpoint de pago.

### 6. Builder — `app/pedidos/builder.py`

**Problema que resuelve:** la construcción completa del pedido (subtotal,
descuento, empaque, envío, armado del resultado final) vivía como un bloque
secuencial dentro del endpoint HTTP.

**Solución:** `PedidoBuilder` expone métodos encadenables
(`.para_cliente()`, `.con_items()`, `.con_cupon()`, `.con_empaque_regalo()`,
`.con_estrategia_envio()`) que configuran el pedido paso a paso, y `.build()`
ejecuta el cálculo real, delegando en Decorator y Strategy, y propaga
cualquier `ValueError` de negocio (cupón o envío inválido) hacia el router.

**Por qué este patrón:** separa la orquestación de la construcción de la
representación final del pedido. El router ya no conoce los detalles
internos de cómo se calcula cada componente del precio.

---

## Organización por routers

Además de los 6 patrones GoF, el proyecto separa los endpoints por dominio
en módulos independientes, dejando `app/main.py` como un simple punto de
arranque que:

- Crea la aplicación FastAPI.
- Monta los archivos estáticos y las plantillas.
- Conecta (`include_router`) los routers de `pedidos` y `pagos`.
- Expone dos endpoints utilitarios propios: consulta de inventario y
  exportación a Excel del historial de pedidos.

Esto permite que cada dominio (pedidos, pagos) crezca de forma
independiente sin que `main.py` deba modificarse.

---

## Endpoints de la API

| Método | Ruta | Descripción | Patrones involucrados |
|---|---|---|---|
| `GET` | `/` | Sirve el panel administrativo (HTML) | — |
| `POST` | `/api/pedidos/` | Crea un pedido nuevo | Builder, Strategy, Decorator |
| `GET` | `/api/pedidos/` | Lista todos los pedidos | — |
| `GET` | `/api/pedidos/{id}` | Consulta un pedido por ID | — |
| `DELETE` | `/api/pedidos/{id}` | Cancela y elimina un pedido pendiente, restituyendo el inventario | — |
| `POST` | `/api/pedidos/{id}/enviar` | Marca un pedido como enviado | State |
| `POST` | `/api/pagos/` | Procesa el pago de un pedido | Factory Method, State, Observer |
| `GET` | `/api/inventario` | Consulta el stock disponible | — |
| `GET` | `/api/pedidos/exportar/excel` | Descarga un archivo `.xlsx` con el historial completo de pedidos | — |

**Reglas de negocio activas:**

- Los cupones `DESC10`, `DESC20` y `BLACKFRIDAY` exigen un monto mínimo de
  compra; si no se alcanza, la API rechaza el pedido con un mensaje
  explicativo.
- El envío gratis solo aplica para compras superiores a un monto mínimo
  configurado en `EnvioGratis`.
- Un pedido solo puede eliminarse mientras esté en estado `"pendiente"`.
- Un pedido no puede marcarse como enviado sin haber sido pagado antes.

---

## Flujo completo de un pedido

```
1. Cliente arma el pedido en el panel → POST /api/pedidos/
   (app/pedidos/router.py)
   ├── pide la estrategia de envío a envios/strategy.py
   ├── delega la construcción a PedidoBuilder
   │      └── PedidoBuilder usa pedidos/decorator.py (cupón + empaque)
   │      └── PedidoBuilder usa la estrategia de envío recibida
   └── se descuenta el inventario (database.py) y se guarda el pedido

2. Cliente paga → POST /api/pagos/ (app/pagos/router.py)
   ├── pide el método de pago correcto a pagos/factory.py
   ├── pide el estado actual a domain_state.py y ejecuta pagar()
   │      └── Si no es válido, lanza EstadoInvalidoError → HTTP 400
   └── notifica a todos los observadores vía pagos/observer.py

3. Se despacha el pedido → POST /api/pedidos/{id}/enviar
   └── domain_state.py valida que el estado actual permita enviar()

4. Se descarga el reporte → GET /api/pedidos/exportar/excel
   └── main.py arma un DataFrame de pandas y devuelve un archivo .xlsx
```

---

## Panel administrativo (frontend)

El frontend (`templates/index.html` + `static/js/app.js`) ofrece:

- Formulario de creación de pedidos con selección de marca, tamaño (con
  precio autocompletado), cupón y empaque de regalo.
- Formulario de procesamiento de pago con campos dinámicos según el método
  elegido.
- Panel de control de pedidos con filtros por estado (todos, pendientes,
  listos para despacho, completados) y acciones contextuales por fila.
- Botón de exportación directa del historial de pedidos a Excel.
- Tarjeta visual de resultado con el desglose completo del pedido
  (subtotal, descuento, empaque, envío, total).

El frontend consume exclusivamente los endpoints listados arriba; ningún
cálculo de negocio se realiza en el cliente.

---
