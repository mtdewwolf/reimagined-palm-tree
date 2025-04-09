from fastapi import FastAPI, WebSocket, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from typing import List, Optional
import sqlite3
import json
import asyncio
from datetime import datetime

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connections
active_connections: List[WebSocket] = []

@app.websocket("/ws/weight")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            # Here we would get the actual weight from the scale
            # For now, we'll just send a dummy weight
            weight = 0.0  # Replace with actual scale reading
            await websocket.send_json({"weight": weight})
            await asyncio.sleep(0.1)
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        active_connections.remove(websocket)

@app.get("/api/weights")
async def get_weights(limit: int = 10):
    conn = sqlite3.connect('weighing_system.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT w.weight, w.timestamp, v.license_plate, u.username
        FROM weight_measurements w
        LEFT JOIN vehicles v ON w.vehicle_id = v.id
        LEFT JOIN users u ON w.operator_id = u.id
        ORDER BY w.timestamp DESC
        LIMIT ?
    ''', (limit,))
    weights = cursor.fetchall()
    conn.close()
    
    return [{
        "weight": w[0],
        "timestamp": w[1],
        "license_plate": w[2],
        "operator": w[3]
    } for w in weights]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 