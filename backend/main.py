from fastapi import FastAPI, WebSocket, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from typing import List, Optional, Tuple, Any
import sqlite3
import json
import asyncio
from datetime import datetime
from .auth import authenticate_user, create_access_token, get_current_user
from pydantic import BaseModel

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database utility functions
def get_db_connection():
    """Returns a database connection with context manager support"""
    return sqlite3.connect('weighing_system.db')

async def execute_transaction(queries: List[Tuple[str, Tuple[Any, ...]]]) -> sqlite3.Cursor:
    """Execute multiple queries in a single transaction"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            for query, params in queries:
                cursor.execute(query, params)
            conn.commit()
            return cursor
        except Exception as e:
            conn.rollback()
            raise e

# WebSocket connections
active_connections: List[WebSocket] = []

# Pydantic models
class Vehicle(BaseModel):
    license_plate: str
    vehicle_type: str
    description: Optional[str] = None

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer", "user": user}

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
async def get_weights(limit: int = 10, current_user: dict = Depends(get_current_user)):
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

@app.get("/api/vehicles")
async def get_vehicles(current_user: dict = Depends(get_current_user)):
    conn = sqlite3.connect('weighing_system.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, license_plate, vehicle_type, description
        FROM vehicles
        ORDER BY license_plate
    ''')
    vehicles = cursor.fetchall()
    conn.close()
    
    return [{
        "id": v[0],
        "license_plate": v[1],
        "vehicle_type": v[2],
        "description": v[3]
    } for v in vehicles]

@app.post("/api/vehicles")
async def create_vehicle(vehicle: Vehicle, current_user: dict = Depends(get_current_user)):
    try:
        await execute_transaction([
            ('''
                INSERT INTO vehicles (license_plate, vehicle_type, description)
                VALUES (?, ?, ?)
            ''', (vehicle.license_plate, vehicle.vehicle_type, vehicle.description)),
            ('''
                INSERT INTO audit_log (user_id, action, details)
                VALUES (?, ?, ?)
            ''', (current_user["id"], 'VEHICLE_CREATED', f"License Plate: {vehicle.license_plate}"))
        ])
        return {"message": "Vehicle created successfully"}
    except sqlite3.IntegrityError as e:
        raise HTTPException(status_code=400, detail="License plate already exists") from e

@app.put("/api/vehicles/{vehicle_id}")
async def update_vehicle(
    vehicle_id: int,
    vehicle: Vehicle,
    current_user: dict = Depends(get_current_user)
):
    try:
        cursor = await execute_transaction([
            ('''
                UPDATE vehicles
                SET license_plate = ?, vehicle_type = ?, description = ?
                WHERE id = ?
            ''', (vehicle.license_plate, vehicle.vehicle_type, vehicle.description, vehicle_id)),
            ('''
                INSERT INTO audit_log (user_id, action, details)
                VALUES (?, ?, ?)
            ''', (current_user["id"], 'VEHICLE_UPDATED', f"ID: {vehicle_id}, License Plate: {vehicle.license_plate}"))
        ])
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Vehicle not found")
            
        return {"message": "Vehicle updated successfully"}
    except sqlite3.IntegrityError as e:
        raise HTTPException(status_code=400, detail="License plate already exists") from e

@app.delete("/api/vehicles/{vehicle_id}")
async def delete_vehicle(vehicle_id: int, current_user: dict = Depends(get_current_user)):
    try:
        # Get vehicle info for audit log
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT license_plate FROM vehicles WHERE id = ?', (vehicle_id,))
            result = cursor.fetchone()
            if not result:
                raise HTTPException(status_code=404, detail="Vehicle not found")
            
            license_plate = result[0]
        
        # Delete vehicle and log the action
        await execute_transaction([
            ('DELETE FROM vehicles WHERE id = ?', (vehicle_id,)),
            ('''
                INSERT INTO audit_log (user_id, action, details)
                VALUES (?, ?, ?)
            ''', (current_user["id"], 'VEHICLE_DELETED', f"ID: {vehicle_id}, License Plate: {license_plate}"))
        ])
        
        return {"message": "Vehicle deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.get("/api/audit-log")
async def get_audit_log(
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
        
    conn = sqlite3.connect('weighing_system.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT a.timestamp, u.username, a.action, a.details
        FROM audit_log a
        LEFT JOIN users u ON a.user_id = u.id
        ORDER BY a.timestamp DESC
        LIMIT ?
    ''', (limit,))
    logs = cursor.fetchall()
    conn.close()
    
    return [{
        "timestamp": l[0],
        "username": l[1],
        "action": l[2],
        "details": l[3]
    } for l in logs]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 