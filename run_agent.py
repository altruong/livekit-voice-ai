"""
Medical Triage Agent Runner
"""
import sys
from agents.medical_triage import entrypoint
from livekit.agents import cli, WorkerOptions

if __name__ == "__main__":
    # Pass through command line arguments (like 'console')
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint)) 