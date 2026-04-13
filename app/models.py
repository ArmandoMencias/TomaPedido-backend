from pydantic import BaseModel
from typing import List, Optional

class Modificadores(BaseModel):
    excluir: List[str] = []
    variantes: dict = {}

class ItemPedido(BaseModel):
    id_item: str
    producto: str
    cantidad: int
    precio_unitario: float
    modificadores: Optional[Modificadores] = None
    notas: str = ""
    estado_cocina: str = "pendiente"

class LoginRequest(BaseModel):
    username: str
    pin: str

# 1. Agregamos este sub-modelo nuevo
class ProductoTicket(BaseModel):
    nombre: str
    precio: float
    ingredientes_elegidos: List[str] = []
    cantidad: int
    preparado: bool = False

class Plato(BaseModel):
    nombre_plato: str
    items: List[ProductoTicket]

# 2. Modificamos tu TicketRequest existente
class TicketRequest(BaseModel):
    cliente: str
    platos: List[Plato]
    total: float
    status: str
    status_cocina: str = "pendiente" # "pendiente" o "listo"
    status_mesero: str = "pendiente"  # "pendiente", "servido", etc.


class Ticket(BaseModel):
    id_ticket: str
    tipo_orden: str
    identificador: str
    estado_cuenta: str
    mesero: str
    fecha_hora: str
    platos: List[Plato]
    total_acumulado: float
    status_cocina: str = "pendiente"
    status_mesero: str = "pendiente"
    