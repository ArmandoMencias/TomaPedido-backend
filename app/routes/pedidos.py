from fastapi import APIRouter, HTTPException
from bson import ObjectId
from app.models import Ticket, Plato, TicketRequest
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
        # Usar 'status' y 'pendiente' exactamente como están en tu JSON
        cursor = db["tickets"].find({"status": {"$in": ["pendiente", "listo"]}})

        pedidos = await cursor.to_list(length=100)
        
        for pedido in pedidos:
            pedido["_id"] = str(pedido["_id"])
            
        return pedidos
    except Exception as e:
        print(f"Error en servidor: {e}")
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
    
# 1. ACTUALIZAMOS OBTENER CUENTA PARA FUSIONAR LAS RONDAS
@router.get("/pedidos/{cliente_nombre}")
async def obtener_cuenta(cliente_nombre: str):
    # Usamos find() en lugar de find_one() para traer TODAS las rondas de Juan
    cursor = db["tickets"].find({
        "cliente": cliente_nombre, 
        "status": {"$in": ["pendiente", "listo"]}
    })
    
    tickets = await cursor.to_list(length=100)
        
    if not tickets:
        return {"cliente": cliente_nombre, "platos": [], "total": 0.0, "status": "nuevo"}

    # Lógica de agrupación (Fusión de rondas)
    todos_los_platos = []
    gran_total = 0.0

    for t in tickets:
        todos_los_platos.extend(t.get("platos", []))
        gran_total += t.get("total", 0.0)

    # Devolvemos al mesero un "Super Ticket" con todo sumado
    return {
        "cliente": cliente_nombre,
        "platos": todos_los_platos,
        "total": gran_total,
        "status": "pendiente" 
    }

@router.post("/pedidos")
async def recibir_pedido(ticket: TicketRequest):
    ticket_dict = ticket.model_dump()
    await db["tickets"].insert_one(ticket_dict)
    return {"mensaje": "Comanda enviada a cocina correctamente"}

# 2. ACTUALIZAMOS EL ESTATUS PARA CERRAR TODAS LAS RONDAS AL COBRAR
@router.put("/pedidos/{cliente_nombre}/status")
async def actualizar_status(cliente_nombre: str, data: dict):
    # Usamos update_many en lugar de update_one.
    # Si el mesero cobra la mesa de Juan, debe cerrar TODAS sus comandas.
    resultado = await db["tickets"].update_many(
        {"cliente": cliente_nombre, "status": {"$in": ["pendiente", "listo"]}},
        {"$set": data}
    )
    
    if resultado.modified_count > 0:
        return {"mensaje": f"Se actualizaron {resultado.modified_count} comandas."}
    
    raise HTTPException(status_code=404, detail="Pedido no encontrado o ya finalizado")
    
@router.get("/clientes/activos")
async def obtener_mesas_consolidadas():
    try:
        pipeline = [
            # 1. Filtramos solo tickets que no han sido pagados
            {"$match": {"status": "pendiente"}},
            # 2. Agrupamos por nombre de cliente
            {"$group": {
                "_id": "$cliente",
                "cliente": {"$first": "$cliente"},
                "total": {"$sum": "$total"},
                # Si alguna de las comandas de Juan está 'lista', avisamos al mesero
                "status_cocina": {"$min": "$status_cocina"} 
            }}
        ]
        
        cursor = db["tickets"].aggregate(pipeline)
        resultado = await cursor.to_list(length=100)

        for mesa in resultado:
            mesa["status"] = "listo" if mesa["status_cocina"] == "listo" else "pendiente"
            
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener mesas: {str(e)}")


@router.put("/pedidos/{cliente_nombre}/cobrar")
async def cobrar_cuenta(cliente_nombre: str):
    try:
        print(f"Iniciando cobro para la mesa: {cliente_nombre}")
        
        # 1. Buscamos todas las rondas activas del cliente
        cursor = db["tickets"].find({
            "cliente": cliente_nombre,
            "status": {"$in": ["pendiente", "listo"]}
        })
        tickets = await cursor.to_list(length=100)
        
        if not tickets:
            raise HTTPException(status_code=404, detail="No hay cuenta activa para este cliente")
            
        # 2. Calculamos el gran total sumando todas las rondas
        gran_total = 0.0
        for t in tickets:
            gran_total += t.get("total", 0.0)
            
        # 3. Actualizamos TODAS las rondas a "pagado"
        resultado = await db["tickets"].update_many(
            {"cliente": cliente_nombre, "status": {"$in": ["pendiente", "listo"]}},
            {"$set": {
                "status": "pagado",
                "estado_cuenta": "cerrada" # Útil para tus reportes de caja
            }}
        )
        
        if resultado.modified_count > 0:
            print(f"Cuenta de {cliente_nombre} pagada. Total: ${gran_total}")
            # Devolvemos un diccionario de strings porque tu Android espera Call<Map<String, String>>
            return {
                "mensaje": "Cuenta cobrada con éxito",
                "total_cobrado": str(gran_total)
            }
            
        raise HTTPException(status_code=500, detail="No se pudieron actualizar los registros")
        
    except Exception as e:
        print(f"Error al cobrar cuenta: {e}")
        raise HTTPException(status_code=500, detail=str(e))
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


@router.put("/comanda/{id_ticket}/listo")
async def marcar_comanda_lista(id_ticket: str):
    try:
        print(f"Buscando comanda para marcar como lista: {id_ticket}")
        
        resultado = await db["tickets"].update_one(
            {"_id": ObjectId(id_ticket)},
            {
                # CAMBIO CORREGIDO: ¡Solo tocamos la cocina! Dejamos la cuenta pendiente.
                "$set": {"status_cocina": "listo"} 
            }
        )
        
        if resultado.matched_count > 0:
            print("Comanda encontrada y procesada.")
            return {"mensaje": "Comanda marcada como lista"}
            
        print("Error: El ID no se encontró en MongoDB.")
        raise HTTPException(status_code=404, detail="Comanda no encontrada en la base de datos")
        
    except Exception as e:
        print(f"Error fatal: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    

@router.put("/pedidos/{cliente_nombre}/cobrar")
async def cobrar_cuenta(cliente_nombre: str):
    try:
        print(f"Iniciando cobro para la mesa: {cliente_nombre}")
        
        # 1. Buscamos todas las rondas activas del cliente
        cursor = db["tickets"].find({
            "cliente": cliente_nombre,
            "status": {"$in": ["pendiente", "listo"]}
        })
        tickets = await cursor.to_list(length=100)
        
        if not tickets:
            raise HTTPException(status_code=404, detail="No hay cuenta activa para este cliente")
            
        # 2. Calculamos el gran total sumando todas las rondas
        gran_total = 0.0
        for t in tickets:
            gran_total += t.get("total", 0.0)
            
        # 3. Actualizamos TODAS las rondas a "pagado"
        resultado = await db["tickets"].update_many(
            {"cliente": cliente_nombre, "status": {"$in": ["pendiente", "listo"]}},
            {"$set": {
                "status": "pagado",
                "estado_cuenta": "cerrada" # Útil para tus reportes de caja
            }}
        )
        
        if resultado.modified_count > 0:
            print(f"Cuenta de {cliente_nombre} pagada. Total: ${gran_total}")
            # Devolvemos un diccionario de strings porque tu Android espera Call<Map<String, String>>
            return {
                "mensaje": "Cuenta cobrada con éxito",
                "total_cobrado": str(gran_total)
            }
            
        raise HTTPException(status_code=500, detail="No se pudieron actualizar los registros")
        
    except Exception as e:
        print(f"Error al cobrar cuenta: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    