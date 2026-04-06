from fastapi import FastAPI
from app.routes import auth, menu, pedidos
from app.database import db

app = FastAPI(title="API Sistema de Comandas")


# Registrar las rutas modulares y agruparlas para que Swagger se vea ordenado
app.include_router(auth.router, tags=["Autenticación"])
app.include_router(menu.router, tags=["Menú"])
app.include_router(pedidos.router, tags=["Operaciones de Pedidos"])
app.include_router(pedidos.router)


@app.get("/")
async def root():
    return {"mensaje": "API funcionando correctamente"}
