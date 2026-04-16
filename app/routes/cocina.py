from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from bson import ObjectId
from app.database import db
from app.websocket import manager

router = APIRouter()

@router.get("/pedidos_activos")
async def obtener_pedidos():
    try:
        cursor = db["tickets"].find({"status": {"$in": ["pendiente", "listo"]}})
        pedidos = await cursor.to_list(length=100)
        for pedido in pedidos:
            pedido["_id"] = str(pedido["_id"])
        return pedidos
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/comanda/{id_ticket}/listo")
async def marcar_comanda_lista(id_ticket: str):
    try:
        resultado = await db["tickets"].update_one(
            {"_id": ObjectId(id_ticket)},
            {"$set": {"status_cocina": "listo"}}
        )
        if resultado.matched_count > 0:
            return {"mensaje": "Comanda marcada como lista"}
        raise HTTPException(status_code=404, detail="Comanda no encontrada")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.websocket("/ws/cocina")
async def websocket_cocina(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)