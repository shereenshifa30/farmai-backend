from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class UserLogin(BaseModel):
    email: str
    password: str

class UserSignup(BaseModel):
    email: str
    password: str

@router.post("/login")
def login(user: UserLogin):
    # ── Will connect to Supabase in next step ──
    return {
        "message": "Login successful",
        "email": user.email,
        "token": "demo-token-123"
    }

@router.post("/signup")
def signup(user: UserSignup):
    # ── Will connect to Supabase in next step ──
    return {
        "message": "Account created successfully",
        "email": user.email,
        "token": "demo-token-123"
    }