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

class Plato(BaseModel):
    nombre_plato: str
    items: List[ItemPedido]

class Ticket(BaseModel):
    id_ticket: str
    tipo_orden: str
    identificador: str
    estado_cuenta: str
    mesero: str
    fecha_hora: str
    platos: List[Plato]
    total_acumulado: float

class LoginRequest(BaseModel):
    username: str
    pin: str