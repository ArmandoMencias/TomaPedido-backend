from fastapi import APIRouter, HTTPException
from bson import ObjectId
from app.models import TicketRequest, Plato
from app.database import db
from app.websocket import manager

router = APIRouter()

@router.post("/pedidos")
async def recibir_pedido(ticket: TicketRequest):
    ticket_dict = ticket.model_dump()
    await db["tickets"].insert_one(ticket_dict)
    
    # Aviso en tiempo real a la cocina
    await manager.broadcast("NUEVO_PEDIDO")
    return {"mensaje": "Comanda enviada a cocina correctamente"}

@router.get("/clientes/activos")
async def obtener_mesas_consolidadas():
    try:
        pipeline = [
            {"$match": {"status": "pendiente"}},
            {"$group": {
                "_id": "$cliente",
                "cliente": {"$first": "$cliente"},
                "total": {"$sum": "$total"},
                "status_cocina": {"$min": "$status_cocina"} 
            }}
        ]
        cursor = db["tickets"].aggregate(pipeline)
        resultado = await cursor.to_list(length=100)
        for mesa in resultado:
            mesa["status"] = "listo" if mesa["status_cocina"] == "listo" else "pendiente"
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pedidos/{cliente_nombre}")
async def obtener_cuenta(cliente_nombre: str):
    cursor = db["tickets"].find({
        "cliente": cliente_nombre, 
        "status": {"$in": ["pendiente", "listo"]}
    })
    tickets = await cursor.to_list(length=100)
    if not tickets:
        return {"cliente": cliente_nombre, "platos": [], "total": 0.0, "status": "nuevo"}

    todos_los_platos = []
    gran_total = 0.0
    for t in tickets:
        todos_los_platos.extend(t.get("platos", []))
        gran_total += t.get("total", 0.0)

    return {
        "cliente": cliente_nombre,
        "platos": todos_los_platos,
        "total": gran_total,
        "status": "pendiente" 
    }

@router.put("/pedidos/{cliente_nombre}/cobrar")
async def cobrar_cuenta(cliente_nombre: str):
    try:
        cursor = db["tickets"].find({
            "cliente": cliente_nombre,
            "status": {"$in": ["pendiente", "listo"]}
        })
        tickets = await cursor.to_list(length=100)
        
        if not tickets:
            raise HTTPException(status_code=404, detail="No hay cuenta activa para este cliente")
            
        gran_total = sum(t.get("total", 0.0) for t in tickets)
            
        resultado = await db["tickets"].update_many(
            {"cliente": cliente_nombre, "status": {"$in": ["pendiente", "listo"]}},
            {"$set": {
                "status": "pagado",
                "estado_cuenta": "cerrada"
            }}
        )
        if resultado.modified_count > 0:
            return {"mensaje": "Cuenta cobrada con éxito", "total_cobrado": str(gran_total)}
        raise HTTPException(status_code=500, detail="No se pudieron actualizar los registros")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/agregar_plato/{id_mongo}")
async def agregar_plato(id_mongo: str, nuevo_plato: Plato):
    # Dejé esta ruta por si la utilizas para agregar platos a un ticket existente
    try:
        resultado = await db["tickets"].update_one(
            {"_id": ObjectId(id_mongo)},
            {"$push": {"platos": nuevo_plato.model_dump()}}
        )
        if resultado.modified_count == 0:
            raise HTTPException(status_code=404, detail="No se encontró el ticket")
        return {"mensaje": "Plato agregado a la nota"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))