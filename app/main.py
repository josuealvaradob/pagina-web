"""
.venv\Scripts\activate.bat
uvicorn app.main:app --reload
"""

import io
import pandas as pd
from datetime import datetime
from pathlib import Path

import fastapi
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import database
from app.pedidos import router as pedidos_router
from app.pagos import router as pagos_router

BASE_DIR = Path(__file__).resolve().parent.parent

app = fastapi.FastAPI(
    title="Los Samarios del Perfume",
    description="API demostrativa con patrones de diseño aplicados a un flujo de e-commerce.",
)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Conectamos las rutas que creamos en los otros archivos
app.include_router(pedidos_router.router, prefix="/api/pedidos", tags=["pedidos"])
app.include_router(pagos_router.router, prefix="/api/pagos", tags=["pagos"])


@app.get("/")
def index(request: fastapi.Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/inventario", tags=["inventario"])
def ver_inventario():
    return database.INVENTARIO


@app.get("/api/pedidos/exportar/excel", tags=["reportes"])
def exportar_pedidos_excel():
    if not database.PEDIDOS:
        raise fastapi.HTTPException(
            status_code=400, detail="No hay pedidos registrados para exportar."
        )

    filas = []
    for p in database.PEDIDOS.values():
        items_str = ", ".join(
            [f"{i['cantidad']}x {i['producto']}" for i in p.get("items", [])]
        )

        filas.append(
            {
                "ID Pedido": p.get("id"),
                "Fecha Creación": p.get("fecha", "N/A"),
                "Cliente": p.get("cliente"),
                "Productos": items_str,
                "Subtotal": p.get("subtotal"),
                "Descuento": p.get("descuento"),
                "Cupón": p.get("cupon") or "Ninguno",
                "Costo Empaque": p.get("costo_empaque"),
                "Tipo Envío": p.get("tipo_envio"),
                "Costo Envío": p.get("costo_envio"),
                "Total Final": p.get("total"),
                "Estado": p.get("estado", "").upper(),
                "Método Pago": (p.get("metodo_pago") or "Pendiente").upper(),
            }
        )

    df = pd.DataFrame(filas)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Pedidos")
    output.seek(0)

    nombre_archivo = f"pedidos_samarios_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    headers = {"Content-Disposition": f"attachment; filename={nombre_archivo}"}

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )
