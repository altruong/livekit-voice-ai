#!/usr/bin/env python3
"""
Test script to verify LiveKit Voice AI setup
"""

import os
import sys
from dotenv import load_dotenv

def check_environment():
    """Check if all required environment variables are set"""
    load_dotenv()
    
    required_vars = [
        "LIVEKIT_URL",
        "LIVEKIT_API_KEY", 
        "LIVEKIT_API_SECRET",
        "OPENAI_API_KEY",
        "DEEPGRAM_API_KEY",
        "CARTESIA_API_KEY"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease add these to your .env file")
        return False
    else:
        print("✅ All required environment variables are set")
        return True

def check_dependencies():
    """Check if all required packages are installed"""
    required_packages = [
        ("livekit.agents", "LiveKit Agents"),
        ("livekit.plugins.openai", "OpenAI Plugin"),
        ("livekit.plugins.deepgram", "Deepgram Plugin"), 
        ("livekit.plugins.cartesia", "Cartesia Plugin"),
        ("livekit.plugins.silero", "Silero Plugin"),
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
    ]
    
    missing_packages = []
    for package, name in required_packages:
        try:
            __import__(package)
            print(f"✅ {name}")
        except ImportError:
            missing_packages.append(name)
            print(f"❌ {name}")
    
    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("Run: pip install -r requirements.txt")
        return False
    else:
        print("\n✅ All required packages are installed")
        return True

def test_agent_import():
    """Test if the medical triage agent can be imported"""
    try:
        import importlib.util
        import importlib
        
        # Add agents directory to path
        agents_path = os.path.join(os.getcwd(), "agents")
        if agents_path not in sys.path:
            sys.path.insert(0, agents_path)
        
        # Try to import the medical triage module
        spec = importlib.util.spec_from_file_location("medical_triage", "agents/medical_triage.py")
        if spec and spec.loader:
            medical_triage = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(medical_triage)
            
            # Check if required classes exist
            if hasattr(medical_triage, 'entrypoint') and hasattr(medical_triage, 'TriageAgent'):
                print("✅ Medical triage agent imports successfully")
                return True
            else:
                print("❌ Medical triage agent missing required classes")
                return False
        else:
            print("❌ Could not find medical triage agent file")
            return False
    except Exception as e:
        print(f"❌ Failed to import medical triage agent: {e}")
        return False

def test_api_endpoints():
    """Test if FastAPI can start properly"""
    try:
        from app.main import app
        from app.api.routes import router
        print("✅ FastAPI application imports successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to import FastAPI application: {e}")
        return False

def main():
    """Run all tests"""
    print("🔍 Testing LiveKit Voice AI Setup\n")
    
    tests = [
        ("Environment Variables", check_environment),
        ("Dependencies", check_dependencies), 
        ("Agent Import", test_agent_import),
        ("API Import", test_api_endpoints),
    ]
    
    all_passed = True
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        if not test_func():
            all_passed = False
    
    print("\n" + "="*50)
    if all_passed:
        print("🎉 All tests passed! Your setup is ready.")
        print("\nNext steps (microservices architecture):")
        print("1. Terminal 1: python run_agent.py dev")
        print("2. Terminal 2: python run.py") 
        print("3. API docs: http://localhost:8000")
        print("4. Web client: http://localhost:8000/client")
    else:
        print("❌ Some tests failed. Please fix the issues above.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 