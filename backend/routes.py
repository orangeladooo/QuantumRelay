"""
routes.py - REST API routes for PQC-Chatt.

  POST /register
  POST /login
  GET  /users
  GET  /messages/{receiver_id}
  POST /messages
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta, timezone
from bson import ObjectId
from passlib.context import CryptContext
from jose import JWTError, jwt
import os

from database import get_db
from models import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    UserResponse,
    SendMessageRequest,
    MessageResponse,
)
from crypto import crypto_service

router = APIRouter()

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": user_id, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    db = get_db()
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token.")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
    user = await db["users"].find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=401, detail="User not found.")
    return user


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(body: RegisterRequest):
    db = get_db()
    if await db["users"].find_one({"username": body.username}):
        raise HTTPException(status_code=400, detail="Username already taken.")
    doc = {
        "username": body.username,
        "password": hash_password(body.password),
        "publicKey": None,
        "createdAt": datetime.now(timezone.utc),
    }
    result = await db["users"].insert_one(doc)
    return TokenResponse(access_token=create_access_token(str(result.inserted_id)))


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest):
    db = get_db()
    user = await db["users"].find_one({"username": body.username})
    if not user or not verify_password(body.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid username or password.")
    return TokenResponse(access_token=create_access_token(str(user["_id"])))


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

@router.get("/users", response_model=list[UserResponse])
async def get_all_users(current_user=Depends(get_current_user)):
    db = get_db()
    users = []
    async for u in db["users"].find({}, {"password": 0}):
        users.append(UserResponse(
            id=str(u["_id"]),
            username=u["username"],
            publicKey=u.get("publicKey"),
            createdAt=u["createdAt"],
        ))
    return users


# ---------------------------------------------------------------------------
# Messages
# ---------------------------------------------------------------------------

@router.get("/messages/{receiver_id}", response_model=list[MessageResponse])
async def get_messages(receiver_id: str, current_user=Depends(get_current_user)):
    db = get_db()
    me = str(current_user["_id"])
    query = {
        "$or": [
            {"senderId": ObjectId(me),       "receiverId": ObjectId(receiver_id)},
            {"senderId": ObjectId(receiver_id), "receiverId": ObjectId(me)},
        ]
    }
    messages = []
    async for m in db["messages"].find(query).sort("createdAt", 1):
        messages.append(MessageResponse(
            id=str(m["_id"]),
            senderId=str(m["senderId"]),
            receiverId=str(m["receiverId"]),
            payload=crypto_service.decrypt(m["payload"]),
            encryptionVersion=m.get("encryptionVersion", 0),
            createdAt=m["createdAt"],
        ))
    return messages


@router.post("/messages", response_model=MessageResponse, status_code=201)
async def send_message(body: SendMessageRequest, current_user=Depends(get_current_user)):
    db = get_db()
    now = datetime.now(timezone.utc)
    doc = {
        "senderId": current_user["_id"],
        "receiverId": ObjectId(body.receiverId),
        "payload": crypto_service.encrypt(body.payload),
        "encryptionVersion": 0,
        "createdAt": now,
    }
    result = await db["messages"].insert_one(doc)
    return MessageResponse(
        id=str(result.inserted_id),
        senderId=str(current_user["_id"]),
        receiverId=body.receiverId,
        payload=body.payload,
        encryptionVersion=0,
        createdAt=now,
    )
