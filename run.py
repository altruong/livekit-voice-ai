"""
LiveKit Voice AI Call Creation API
Pure API service that creates calls for other services to use.
The agent worker should be run separately: python run_agent.py dev
"""
import uvicorn

if __name__ == "__main__":
    print("🔗 LiveKit Call Creation API")
    print("📋 Creates voice call rooms for other services")
    print("🌐 Also serves web client at http://localhost:8000")
    print("⚠️  Make sure to run the agent worker separately:")
    print("   python run_agent.py dev")
    print()
    
    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,  # Enable reload for development
        log_level="info"
    )