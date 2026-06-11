from fastapi import APIRouter, HTTPException
from app.models.schemas import LoginRequest, LoginResponse
import sqlite3
from pathlib import Path

router = APIRouter()
DB_PATH = Path(__file__).parent.parent.parent / "data" / "mall.db"

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE email = ? AND password = ?",
            (request.email, request.password)
        ).fetchone()
    finally:
        conn.close()
    
    if not row:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    return LoginResponse(role=row["role"], email=row["email"])
