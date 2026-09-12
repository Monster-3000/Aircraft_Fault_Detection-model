import uuid
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from backend.database import get_db_connection, hash_password

router = APIRouter()

class RegisterRequest(BaseModel):
    username: str
    password: str
    role: str

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/register")
def register(req: RegisterRequest):
    if req.role not in ["Admin", "Normal Inspector"]:
        raise HTTPException(status_code=400, detail="Invalid role specified.")
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if user exists
    cursor.execute("SELECT * FROM users WHERE username = ?", (req.username,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Username already exists.")
        
    cursor.execute(
        "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
        (req.username, hash_password(req.password), req.role)
    )
    conn.commit()
    conn.close()
    return {"message": "Account created successfully!"}

@router.post("/login")
def login(req: LoginRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT * FROM users WHERE username = ? AND password_hash = ?",
        (req.username, hash_password(req.password))
    )
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        raise HTTPException(status_code=401, detail="Invalid username or password.")
        
    # Generate session token
    token = str(uuid.uuid4())
    cursor.execute(
        "INSERT INTO sessions (token, username) VALUES (?, ?)",
        (token, user["username"])
    )
    conn.commit()
    conn.close()
    
    return {
        "token": token,
        "username": user["username"],
        "role": user["role"]
    }

@router.get("/me")
def get_current_user(token: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT users.username, users.role 
        FROM sessions 
        JOIN users ON sessions.username = users.username 
        WHERE sessions.token = ?
    """, (token,))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired session.")
        
    return {"username": user["username"], "role": user["role"]}
