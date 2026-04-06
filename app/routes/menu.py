from fastapi import APIRouter, HTTPException
from app.database import db

router = APIRouter()

@router.get("/menu")
async def obtener_menu():
    try:
        coleccion = db.menu
        cursor = coleccion.find({"disponible": True})
        lista_menu = await cursor.to_list(length=100)
        
        for producto in lista_menu:
            producto["_id"] = str(producto["_id"])
            
        return lista_menu
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))