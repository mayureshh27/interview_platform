from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import Dict, Any
import json
import logging
import uuid

from app.db.session import get_db
from app.services.webrtc import WebRTCService

router = APIRouter()
logger = logging.getLogger(__name__)

# Create a WebRTC service instance
webrtc_service = WebRTCService()

@router.websocket("/ws/{connection_id}")
async def websocket_endpoint(websocket: WebSocket, connection_id: str):
    """WebSocket endpoint for WebRTC signaling"""
    if not connection_id:
        connection_id = str(uuid.uuid4())
    
    try:
        # Register the websocket connection
        await webrtc_service.register_websocket(connection_id, websocket)
        
        # Send connection ID to the client
        await websocket.send_json({"type": "connection_id", "id": connection_id})
        
        # Handle messages
        while True:
            try:
                # Receive message from the client
                message = await websocket.receive_json()
                
                # Process the message
                await webrtc_service.handle_websocket_message(connection_id, message)
                
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received from {connection_id}")
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for {connection_id}")
        await webrtc_service.close_peer_connection(connection_id)
        
    except Exception as e:
        logger.error(f"Error in websocket connection for {connection_id}: {e}")
        await webrtc_service.close_peer_connection(connection_id)