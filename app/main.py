from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.api.routes import router

app = FastAPI(
    title="LiveKit Call Creation API",
    description="API service for creating voice call rooms with medical triage agents",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)

# Serve static files for web client
app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve web client at root for easy testing
@app.get("/client")
async def get_web_client():
    """Serve the web client for testing voice calls"""
    return FileResponse('static/index.html')