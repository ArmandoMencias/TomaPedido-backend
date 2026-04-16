from fastapi import FastAPI
from app.routes import auth, menu, meseros, cocina
from app.database import db

app = FastAPI(title="API Sistema de Comandas")

app.include_router(meseros.router, tags=["Meseros"])
app.include_router(cocina.router, tags=["Cocina"])
app.include_router(auth.router, tags=["Autenticación"])
app.include_router(menu.router, tags=["Menú"])

@app.get("/")
async def root():
    return {"mensaje": "API funcionando correctamente"}