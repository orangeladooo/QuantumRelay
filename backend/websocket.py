"""
websocket.py - Real-time chat over WebSocket for PQC-Chatt.

Endpoint: /ws/{user_id}

Clients connect with their JWT in the query param:
  ws://host/ws/<user_id>?token=<jwt>

On connect  -> user added to active connections
On message  -> JSON payload { receiverId, payload }
              message saved to DB, forwarded to receiver if online
On disconnect -> user removed from active connections
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status
from jose import JWTError, jwt
from bson import ObjectId
from datetime import datetime, timezone
import json
import os

from database import get_db
from crypto import crypto_service

router = APIRouter()

SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
ALGORITHM = "HS256"

# user_id (str) -> WebSocket
active_connections: dict[str, WebSocket] = {}


# ---------------------------------------------------------------------------
# Auth helper
# ---------------------------------------------------------------------------

def _verify_token(token: str) -> str | None:
    """Return user_id string if token is valid, else None."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None


# ---------------------------------------------------------------------------
# WebSocket endpoint
# ---------------------------------------------------------------------------

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str,
    token: str = Query(...),
):
    # Authenticate
    token_user_id = _verify_token(token)
    if not token_user_id or token_user_id != user_id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    active_connections[user_id] = websocket
    print(f"[WS] User {user_id} connected. Online: {list(active_connections.keys())}")

    db = get_db()

    try:
        while True:
            raw = await websocket.receive_text()

            try:
                data = json.loads(raw)
                receiver_id: str = data["receiverId"]
                payload: str = data["payload"]
            except (KeyError, json.JSONDecodeError):
                await websocket.send_text(json.dumps({"error": "Invalid message format."}))
                continue

            # Persist to DB
            now = datetime.now(timezone.utc)
            doc = {
                "senderId": ObjectId(user_id),
                "receiverId": ObjectId(receiver_id),
                "payload": crypto_service.encrypt(payload),
                "encryptionVersion": 0,
                "createdAt": now,
            }
            result = await db["messages"].insert_one(doc)

            # Build outgoing message
            out = json.dumps({
                "id": str(result.inserted_id),
                "senderId": user_id,
                "receiverId": receiver_id,
                "payload": payload,
                "encryptionVersion": 0,
                "createdAt": now.isoformat(),
            })

            # Forward to receiver if online
            if receiver_id in active_connections:
                try:
                    await active_connections[receiver_id].send_text(out)
                except Exception:
                    pass

            # Echo back to sender as confirmation
            await websocket.send_text(out)

    except WebSocketDisconnect:
        active_connections.pop(user_id, None)
        print(f"[WS] User {user_id} disconnected. Online: {list(active_connections.keys())}")
