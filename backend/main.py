"""
main.py - FastAPI entry point for PQC-Chatt.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from database import connect_db, close_db
from routes import router as http_router
from websocket import router as ws_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    yield
    await close_db()


app = FastAPI(
    title="PQC-Chatt",
    description="Post-Quantum secure chat app",
    version="0.1.0",
    lifespan=lifespan,
)

# Allow all origins in dev — restrict in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(http_router)
app.include_router(ws_router)


@app.get("/")
async def root():
    return {"status": "PQC-Chatt backend running"}
