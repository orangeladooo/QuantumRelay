"""
models.py - Pydantic schemas for PQC-Chatt.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------

class UserResponse(BaseModel):
    id: str
    username: str
    publicKey: Optional[str] = None
    createdAt: datetime


# ---------------------------------------------------------------------------
# Message
# ---------------------------------------------------------------------------

class SendMessageRequest(BaseModel):
    receiverId: str
    payload: str = Field(..., min_length=1)


class MessageResponse(BaseModel):
    id: str
    senderId: str
    receiverId: str
    payload: str
    encryptionVersion: int
    createdAt: datetime


# ---------------------------------------------------------------------------
# WebSocket payload
# ---------------------------------------------------------------------------

class WSMessage(BaseModel):
    receiverId: str
    payload: str
