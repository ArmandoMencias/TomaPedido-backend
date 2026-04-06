from fastapi import APIRouter, HTTPException
from app.models import LoginRequest
from app.database import db

router = APIRouter()

@router.post("/login")
async def login(req: LoginRequest):
    user = await db.usuarios.find_one({"username": req.username, "pin": req.pin})
    
    if user:
        return {
            "status": "success",
            "nombre": user["nombre_real"],
            "rol": user["rol"]
        }
    raise HTTPException(status_code=401, detail="Usuario o PIN incorrectos")