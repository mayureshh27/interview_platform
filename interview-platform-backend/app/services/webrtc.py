# app/services/webrtc.py
import asyncio
import json
import logging
import uuid
from typing import Dict, List, Optional, Set

import cv2
import numpy as np
from aiortc import (
    MediaStreamTrack, RTCPeerConnection, RTCSessionDescription,
    VideoStreamTrack
)
from aiortc.contrib.media import MediaBlackhole, MediaRecorder, MediaRelay
from av import VideoFrame
from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect

from app.core.config import settings
from app.services.facial_analysis import FacialAnalysisService

logger = logging.getLogger(__name__)

class VideoTransformTrack(MediaStreamTrack):
    """
    A video stream track that transforms frames from an another track and
    analyzes them using FacialAnalysisService.
    """
    kind = "video"

    def __init__(self, track, analysis_service):
        super().__init__()
        self.track = track
        self.analysis_service = analysis_service
        self.frame_count = 0
        self.last_frame = None

    async def recv(self):
        frame = await self.track.recv()
        self.frame_count += 1
        
        # Process every 30th frame for analysis (adjust based on performance needs)
        if self.frame_count % 30 == 0:
            # Convert frame to numpy array for analysis
            img = frame.to_ndarray(format="bgr24")
            self.last_frame = img.copy()
            
            # Run facial analysis (non-blocking)
            asyncio.create_task(self.analysis_service.process_frame(img))
        
        return frame

class WebRTCService:
    def __init__(self):
        self.connections: Dict[str, RTCPeerConnection] = {}
        self.room_participants: Dict[str, Set[str]] = {}  # room_id -> set of connection_ids
        self.relays = {}
        self.analysis_services: Dict[str, FacialAnalysisService] = {}
        self.recorders: Dict[str, MediaRecorder] = {}
        self.websocket_connections: Dict[str, WebSocket] = {}
        
    async def create_peer_connection(self, connection_id: str, room_id: str) -> RTCPeerConnection:
        """Create a new WebRTC peer connection"""
        self._ensure_room_exists(room_id)
        
        # Create peer connection with STUN/TURN servers
        ice_servers = [{"urls": server} for server in settings.STUN_SERVERS]
        ice_servers.extend(settings.TURN_SERVERS)
        
        pc = RTCPeerConnection(configuration={"iceServers": ice_servers})
        
        # Store connection
        self.connections[connection_id] = pc
        self.room_participants[room_id].add(connection_id)
        
        # Create media relay for this connection
        self.relays[connection_id] = MediaRelay()
        
        # Create facial analysis service for this connection
        self.analysis_services[connection_id] = FacialAnalysisService()
        
        # Handle ICE connection state changes
        @pc.on("iceconnectionstatechange")
        async def on_iceconnectionstatechange():
            logger.info(f"ICE connection state for {connection_id}: {pc.iceConnectionState}")
            if pc.iceConnectionState == "failed" or pc.iceConnectionState == "closed":
                await self.close_peer_connection(connection_id)
        
        # Handle data channel
        @pc.on("datachannel")
        def on_datachannel(channel):
            logger.info(f"Data channel established for {connection_id}: {channel.label}")
            
            @channel.on("message")
            def on_message(message):
                # Handle data channel messages
                try:
                    data = json.loads(message)
                    logger.info(f"Received message from {connection_id}: {data}")
                    
                    # Process message based on type
                    if data.get("type") == "chat":
                        # Broadcast chat message to room participants
                        asyncio.create_task(self._broadcast_to_room(
                            room_id, 
                            {
                                "type": "chat",
                                "from": connection_id,
                                "message": data.get("message")
                            },
                            exclude=[connection_id]
                        ))
                except Exception as e:
                    logger.error(f"Error handling data channel message: {e}")
        
        return pc
    
    async def handle_offer(self, connection_id: str, room_id: str, offer: dict) -> dict:
        """Handle SDP offer from client"""
        try:
            pc = self.connections.get(connection_id)
            if not pc:
                pc = await self.create_peer_connection(connection_id, room_id)
            
            # Set remote description
            await pc.setRemoteDescription(RTCSessionDescription(
                sdp=offer["sdp"], type=offer["type"]
            ))
            
            # Create answer
            answer = await pc.createAnswer()
            await pc.setLocalDescription(answer)
            
            # Set up media recording
            self._setup_recorder(connection_id, room_id)
            
            # Return answer to client
            return {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
            
        except Exception as e:
            logger.error(f"Error handling offer: {e}")
            raise
    
    async def handle_ice_candidate(self, connection_id: str, candidate: dict) -> None:
        """Handle ICE candidate from client"""
        try:
            pc = self.connections.get(connection_id)
            if pc:
                await pc.addIceCandidate(candidate)
            else:
                logger.warning(f"Received ICE candidate for unknown connection: {connection_id}")
        except Exception as e:
            logger.error(f"Error handling ICE candidate: {e}")
            raise
    
    async def close_peer_connection(self, connection_id: str) -> None:
        """Close WebRTC peer connection"""
        try:
            # Close recorder if exists
            if connection_id in self.recorders:
                await self.recorders[connection_id].stop()
                del self.recorders[connection_id]
            
            # Close peer connection
            pc = self.connections.get(connection_id)
            if pc:
                await pc.close()
                del self.connections[connection_id]
            
            # Remove from relays
            if connection_id in self.relays:
                del self.relays[connection_id]
            
            # Remove from analysis services
            if connection_id in self.analysis_services:
                analysis_service = self.analysis_services[connection_id]
                # Get analysis summary before deleting
                summary = analysis_service.get_analysis_summary()
                del self.analysis_services[connection_id]
                return summary
            
            # Remove from room participants
            for room_id, participants in self.room_participants.items():
                if connection_id in participants:
                    participants.remove(connection_id)
                    # Notify other participants about the leave
                    await self._broadcast_to_room(
                        room_id,
                        {"type": "user_left", "userId": connection_id},
                        exclude=[]
                    )
            
            # Remove websocket connection
            if connection_id in self.websocket_connections:
                ws = self.websocket_connections[connection_id]
                await ws.close()
                del self.websocket_connections[connection_id]
                
        except Exception as e:
            logger.error(f"Error closing peer connection: {e}")
    
    def _ensure_room_exists(self, room_id: str) -> None:
        """Ensure that a room exists in the mapping"""
        if room_id not in self.room_participants:
            self.room_participants[room_id] = set()
    
    def _setup_recorder(self, connection_id: str, room_id: str) -> None:
        """Set up media recording for the connection"""
        pc = self.connections.get(connection_id)
        if not pc:
            return
        
        # Create a media recorder
        recorder_path = f"recordings/{room_id}/{connection_id}_{uuid.uuid4()}.mp4"
        recorder = MediaRecorder(recorder_path)
        self.recorders[connection_id] = recorder
        
        # Add transform track for video analysis
        for transceiver in pc.getTransceivers():
            if transceiver.receiver and transceiver.receiver.track:
                track = transceiver.receiver.track
                if track.kind == "video":
                    # Create analysis track
                    analysis_service = self.analysis_services[connection_id]
                    transform_track = VideoTransformTrack(
                        track=track,
                        analysis_service=analysis_service
                    )
                    
                    # Add track to recorder
                    recorder.addTrack(transform_track)
                elif track.kind == "audio":
                    # Add audio track directly
                    recorder.addTrack(track)
        
        # Start recording
        recorder.start()
    
    async def register_websocket(self, connection_id: str, websocket: WebSocket) -> None:
        """Register a websocket connection for signaling"""
        await websocket.accept()
        self.websocket_connections[connection_id] = websocket
    
    async def handle_websocket_message(self, connection_id: str, message: dict) -> None:
        """Handle a message from the websocket"""
        try:
            message_type = message.get("type")
            room_id = message.get("roomId")
            
            if not room_id:
                logger.error(f"Missing roomId in message: {message}")
                return
            
            if message_type == "join":
                # Client is joining the room
                user_info = message.get("userInfo", {})
                
                # Add to room participants
                self._ensure_room_exists(room_id)
                self.room_participants[room_id].add(connection_id)
                
                # Notify other participants
                await self._broadcast_to_room(
                    room_id, 
                    {
                        "type": "user_joined",
                        "userId": connection_id,
                        "userInfo": user_info
                    },
                    exclude=[connection_id]
                )
                
                # Send room participants to the new user
                await self._send_to_connection(
                    connection_id,
                    {
                        "type": "room_users",
                        "users": list(self.room_participants[room_id])
                    }
                )
                
            elif message_type == "offer":
                # Client is sending an offer
                offer = message.get("offer")
                if offer:
                    answer = await self.handle_offer(connection_id, room_id, offer)
                    await self._send_to_connection(
                        connection_id,
                        {
                            "type": "answer",
                            "answer": answer
                        }
                    )
                
            elif message_type == "ice_candidate":
                # Client is sending an ICE candidate
                candidate = message.get("candidate")
                if candidate:
                    await self.handle_ice_candidate(connection_id, candidate)
                
            elif message_type == "leave":
                # Client is leaving the room
                summary = await self.close_peer_connection(connection_id)
                
                # Send analysis summary if available
                if summary:
                    await self._send_to_connection(
                        connection_id,
                        {
                            "type": "analysis_summary",
                            "summary": summary
                        }
                    )
                
        except Exception as e:
            logger.error(f"Error handling websocket message: {e}")
    
    async def _send_to_connection(self, connection_id: str, message: dict) -> None:
        """Send a message to a specific connection"""
        ws = self.websocket_connections.get(connection_id)
        if ws:
            try:
                await ws.send_json(message)
            except WebSocketDisconnect:
                await self.close_peer_connection(connection_id)
            except Exception as e:
                logger.error(f"Error sending to connection {connection_id}: {e}")
    
    async def _broadcast_to_room(self, room_id: str, message: dict, exclude: List[str] = None) -> None:
        """Broadcast a message to all participants in a room"""
        if exclude is None:
            exclude = []
            
        if room_id not in self.room_participants:
            return
            
        for connection_id in self.room_participants[room_id]:
            if connection_id not in exclude:
                await self._send_to_connection(connection_id, message)