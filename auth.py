import jwt
import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET", "anyrandomstring123")

CLEARANCE_ACCESS = {
    "intern":  ["intern"],
    "manager": ["intern", "manager"],   # ← add this line
    "exec":    ["intern", "manager", "exec"],  # ← exec sees everything
}

MOCK_USERS = {
    "alice": {"password": "pass123", "clearance": "intern"},
    "carol": {"password": "pass789", "clearance": "manager"},  # ← new user
    "bob":   {"password": "pass456", "clearance": "exec"},
}

def create_token(username: str, clearance: str) -> str:
    payload = {
        "username":  username,
        "clearance": clearance,
        "exp":       datetime.now(timezone.utc) + timedelta(hours=8)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])

def get_allowed_clearances(user_clearance: str) -> list:
    return CLEARANCE_ACCESS.get(user_clearance, ["intern"])

def authenticate_user(username: str, password: str):
    user = MOCK_USERS.get(username)
    if not user or user["password"] != password:
        return None
    return {"username": username, "clearance": user["clearance"]}