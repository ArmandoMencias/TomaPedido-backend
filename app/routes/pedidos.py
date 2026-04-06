from fastapi import APIRouter, HTTPException
from bson import ObjectId
from app.models import Ticket, Plato
from app.database import db

router = APIRouter()

@router.post("/crear_pedido")
async def crear_pedido(ticket: Ticket):
    try:
        coleccion = db.tickets
        resultado = await coleccion.insert_one(ticket.model_dump())
        return {
            "mensaje": "Pedido enviado a cocina exitosamente", 
            "id_mongo": str(resultado.inserted_id)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al guardar: {str(e)}")

@router.get("/pedidos_activos")
async def obtener_pedidos():
    try:
        coleccion = db.tickets
        cursor = coleccion.find({"estado_cuenta": "abierta"})
        pedidos = await cursor.to_list(length=100)
        
        for pedido in pedidos:
            pedido["_id"] = str(pedido["_id"])
            
        return pedidos
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al consultar: {str(e)}")

@router.patch("/agregar_plato/{id_mongo}")
async def agregar_plato(id_mongo: str, nuevo_plato: Plato):
    try:
        coleccion = db.tickets
        resultado = await coleccion.update_one(
            {"_id": ObjectId(id_mongo)},
            {"$push": {"platos": nuevo_plato.model_dump()}}
        )
        
        if resultado.modified_count == 0:
            raise HTTPException(status_code=404, detail="No se encontró el ticket")
            
        return {"mensaje": "Plato agregado a la nota"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.patch("/cerrar_cuenta/{id_mongo}")
async def cerrar_cuenta(id_mongo: str):
    try:
        coleccion = db.tickets
        ticket = await coleccion.find_one({"_id": ObjectId(id_mongo)})
        
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket no encontrado")
        
        gran_total = 0
        for plato in ticket.get("platos", []):
            for item in plato.get("items", []):
                gran_total += item.get("precio_unitario", 0) * item.get("cantidad", 0)
        
        resultado = await coleccion.update_one(
            {"_id": ObjectId(id_mongo)},
            {
                "$set": {
                    "total_acumulado": gran_total,
                    "estado_cuenta": "cerrada"
                }
            }
        )
        
        return {
            "mensaje": "Cuenta cerrada con éxito",
            "total_a_cobrar": gran_total,
            "id_ticket": ticket.get("id_ticket")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))