from fastapi import APIRouter, HTTPException, Request, BackgroundTasks, Depends
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import json
import uuid
import logging
from datetime import datetime
from typing import Dict, Optional, List
from livekit.api import AccessToken, VideoGrants, LiveKitAPI, CreateRoomRequest, WebhookReceiver, TokenVerifier

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Configuration
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")
LIVEKIT_URL = os.getenv("LIVEKIT_URL", "wss://localhost:7880")

if not LIVEKIT_API_KEY or not LIVEKIT_API_SECRET:
    logger.warning("LiveKit credentials not configured - some features may not work")

# Global state for active calls (use Redis in production)
active_calls: Dict[str, Dict] = {}
agent_metrics: Dict[str, int] = {"total_calls": 0, "active_sessions": 0, "failed_sessions": 0}

# Initialize webhook receiver
webhook_receiver = WebhookReceiver(
    TokenVerifier(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
) if LIVEKIT_API_KEY and LIVEKIT_API_SECRET else None

# Request/Response Models
class TokenRequest(BaseModel):
    room_name: str
    participant_name: str
    metadata: Optional[dict] = None

class TokenResponse(BaseModel):
    token: str
    url: str
    room_name: str

class StartCallRequest(BaseModel):
    patient_name: Optional[str] = None
    agent_type: str = "medical_triage"
    metadata: Optional[dict] = None
    
class CallResponse(BaseModel):
    call_id: str
    room_name: str
    status: str
    message: str
    participant_token: Optional[str] = None
    livekit_url: Optional[str] = None

class RoomInfo(BaseModel):
    name: str
    max_participants: int = 10
    empty_timeout: int = 600  # 10 minutes

# Dependency for LiveKit API
async def get_livekit_api():
    """Get LiveKit API client"""
    if not LIVEKIT_API_KEY or not LIVEKIT_API_SECRET:
        raise HTTPException(status_code=500, detail="LiveKit credentials not configured")
    
    return LiveKitAPI(LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET)

@router.get("/")
async def root():
    """API documentation and service info"""
    return {
        "service": "LiveKit Voice AI Call Creation API",
        "version": "2.0.0",
        "description": "Production-ready FastAPI server for LiveKit voice agents",
        "architecture": {
            "coordination_layer": "FastAPI REST API",
            "realtime_layer": "LiveKit WebRTC",
            "ai_layer": "Voice Agents (STT→LLM→TTS)"
        },
        "endpoints": {
            "POST /calls/start": "Create new voice call with agent",
            "POST /token": "Generate LiveKit access token",
            "POST /rooms": "Create LiveKit room",
            "GET /health": "Health check with detailed metrics",
            "POST /livekit/webhook": "LiveKit webhook handler",
            "GET /metrics": "Agent performance metrics"
        },
        "agent_worker_required": "python run_agent.py dev",
        "documentation": "https://docs.livekit.io/agents/build/"
    }

@router.get("/health")
async def health_check():
    """Comprehensive health check for monitoring"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "livekit-voice-ai",
        "components": {}
    }
    
        # Check LiveKit configuration
    if LIVEKIT_API_KEY and LIVEKIT_API_SECRET:
        health_status["components"]["livekit_config"] = "configured"
        health_status["components"]["livekit_api"] = "available"
    else:
        health_status["components"]["livekit_config"] = "missing_credentials"
        health_status["status"] = "degraded"
    
    # Add call metrics
    health_status["metrics"] = {
        "active_calls": len([c for c in active_calls.values() if c["status"] != "ended"]),
        "total_calls": agent_metrics["total_calls"],
        "active_sessions": agent_metrics["active_sessions"],
        "failed_sessions": agent_metrics["failed_sessions"]
    }
    
    return health_status

@router.post("/token", response_model=TokenResponse)
async def create_token(request: TokenRequest):
    """Generate LiveKit access token with enhanced security"""
    try:
        if not LIVEKIT_API_KEY or not LIVEKIT_API_SECRET:
            raise HTTPException(
                status_code=500,
                detail="LiveKit credentials not configured"
            )

        # Enhanced token with metadata
        token = AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        
        # Set participant identity and metadata
        token = token.with_identity(request.participant_name)
        if request.metadata:
            token = token.with_metadata(json.dumps(request.metadata))
        
        # Configure video grants with appropriate permissions
        grants = VideoGrants(
            room_join=True,
            room=request.room_name,
            can_publish=True,
            can_subscribe=True,
            # Production security settings
            can_publish_data=True,  # For agent communication
        )
        token = token.with_grants(grants)

        logger.info(f"Generated token for {request.participant_name} in room {request.room_name}")

        return TokenResponse(
            token=token.to_jwt(),
            url=LIVEKIT_URL,
            room_name=request.room_name
        )

    except Exception as e:
        logger.error(f"Token generation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create token: {str(e)}"
        )

@router.post("/rooms")
async def create_room(room_info: RoomInfo, lk_api = Depends(get_livekit_api)):
    """Create a LiveKit room with configuration"""
    try:
        room_request = CreateRoomRequest(
            name=room_info.name,
            max_participants=room_info.max_participants,
            empty_timeout=room_info.empty_timeout,
            metadata=json.dumps({
                "agent_enabled": True,
                "created_by": "fastapi_server",
                "created_at": datetime.now().isoformat()
            })
        )
        
        room = await lk_api.room.create_room(room_request)
            
        logger.info(f"Created room: {room.name}")
        return {"room": room, "status": "created"}
        
    except Exception as e:
        logger.error(f"Room creation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create room: {str(e)}"
        )

@router.post("/calls/start", response_model=CallResponse)
async def start_voice_call(request: StartCallRequest):
    """Start a new voice call with agent dispatch"""
    try:
        # Generate identifiers
        call_id = str(uuid.uuid4())
        room_name = f"{request.agent_type}-{call_id[:8]}"
        patient_name = request.patient_name or f"Patient-{call_id[:8]}"
        
        # Enhanced call metadata
        call_metadata = {
            "agent_type": request.agent_type,
            "patient_name": patient_name,
            "custom_metadata": request.metadata or {},
            "session_config": {
                "enable_interruptions": True,
                "response_timeout": 30,
                "max_duration": 1800  # 30 minutes
            }
        }
        
        # Store call information
        active_calls[call_id] = {
            "room_name": room_name,
            "patient_name": patient_name,
            "agent_type": request.agent_type,
            "status": "initializing",
            "metadata": call_metadata,
            "created_at": datetime.now().isoformat(),
            "participants": []
        }
        
        # Generate participant token immediately
        token_request = TokenRequest(
            room_name=room_name,
            participant_name=patient_name,
            metadata=call_metadata
        )
        token_response = await create_token(token_request)
        
        # Update metrics
        agent_metrics["total_calls"] += 1
        agent_metrics["active_sessions"] += 1
        
        logger.info(f"Created voice call: {call_id} in room {room_name}")
        
        return CallResponse(
            call_id=call_id,
            room_name=room_name,
            status="ready",
            message=f"Voice call ready for {patient_name}. Agent will join automatically.",
            participant_token=token_response.token,
            livekit_url=LIVEKIT_URL
        )
            
    except Exception as e:
        agent_metrics["failed_sessions"] += 1
        logger.error(f"Call creation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create call: {str(e)}"
        )

@router.post("/livekit/webhook")
async def livekit_webhook(request: Request, background_tasks: BackgroundTasks):
    """Handle LiveKit webhook events for monitoring and lifecycle management"""
    if not webhook_receiver:
        raise HTTPException(status_code=500, detail="Webhook receiver not configured")
    
    # Verify webhook authentication
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    body = await request.body()
    
    try:
        # Verify and parse webhook event
        event = webhook_receiver.receive(body.decode("utf-8"), auth_header)
        
        # Process event asynchronously
        background_tasks.add_task(process_webhook_event, event)
        
        logger.info(f"Received webhook event: {event.event}")
        return {"status": "ok", "event": event.event}
        
    except Exception as e:
        logger.error(f"Webhook verification failed: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

async def process_webhook_event(event):
    """Process LiveKit webhook events"""
    try:
        event_type = event.event
        room_name = getattr(event, 'room', {}).get('name', '')
        
        logger.info(f"Processing webhook event: {event_type} for room: {room_name}")
        
        if event_type == "room_started":
            # Update call status when room starts
            for call_id, call_info in active_calls.items():
                if call_info["room_name"] == room_name:
                    call_info["status"] = "active"
                    break
                    
        elif event_type == "participant_joined":
            participant = event.participant
            # Track participant joins
            for call_id, call_info in active_calls.items():
                if call_info["room_name"] == room_name:
                    call_info["participants"].append({
                        "identity": participant.identity,
                        "joined_at": datetime.now().isoformat()
                    })
                    break
                    
        elif event_type == "room_finished":
            # Clean up finished rooms
            for call_id, call_info in active_calls.items():
                if call_info["room_name"] == room_name:
                    call_info["status"] = "ended"
                    agent_metrics["active_sessions"] = max(0, agent_metrics["active_sessions"] - 1)
                    break
                    
    except Exception as e:
        logger.error(f"Webhook event processing failed: {str(e)}")

@router.get("/metrics")
async def get_metrics():
    """Get comprehensive agent and system metrics"""
    return {
        "agent_metrics": agent_metrics,
        "call_metrics": {
            "total_calls": len(active_calls),
            "active_calls": len([c for c in active_calls.values() if c["status"] not in ["ended", "failed"]]),
            "ended_calls": len([c for c in active_calls.values() if c["status"] == "ended"]),
            "failed_calls": len([c for c in active_calls.values() if c["status"] == "failed"])
        },
        "system_metrics": {
            "livekit_url": LIVEKIT_URL,
            "credentials_configured": bool(LIVEKIT_API_KEY and LIVEKIT_API_SECRET),
            "webhook_configured": webhook_receiver is not None
        }
    }

# Legacy endpoints for backward compatibility
@router.get("/agents")
async def get_available_agents():
    """Get list of available voice agents"""
    return [
        {
            "name": "medical_triage",
            "description": "Medical Office Triage Agent - Routes patients to appropriate departments",
            "status": "available",
            "capabilities": ["voice_interaction", "symptom_collection", "department_routing"]
        }
    ]

@router.get("/calls/{call_id}")
async def get_call_status(call_id: str):
    """Get detailed status of a specific call"""
    if call_id not in active_calls:
        raise HTTPException(status_code=404, detail="Call not found")
    
    return active_calls[call_id]

@router.post("/calls/{call_id}/end")
async def end_call(call_id: str):
    """End a specific call and update metrics"""
    if call_id not in active_calls:
        raise HTTPException(status_code=404, detail="Call not found")
    
    call_info = active_calls[call_id]
    call_info["status"] = "ended"
    call_info["ended_at"] = datetime.now().isoformat()
    
    # Update metrics
    agent_metrics["active_sessions"] = max(0, agent_metrics["active_sessions"] - 1)
    
    logger.info(f"Ended call: {call_id}")
    return {
        "call_id": call_id,
        "status": "ended",
        "message": "Call ended successfully"
    }

@router.get("/calls")
async def list_calls():
    """List all calls with filtering and pagination"""
    active = []
    ended = []
    
    for call_id, call_info in active_calls.items():
        call_data = {
            "call_id": call_id,
            **call_info
        }
        
        if call_info["status"] == "ended":
            ended.append(call_data)
        else:
            active.append(call_data)
    
    return {
        "active_calls": active,
        "ended_calls": ended,
        "summary": {
            "total_active": len(active),
            "total_ended": len(ended),
            "total_all_time": agent_metrics["total_calls"]
        }
    }