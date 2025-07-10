"""
Simple Voice AI Agent
Basic STT -> LLM -> TTS pipeline
"""
from dotenv import load_dotenv
from livekit import agents
from livekit.agents import voice
from livekit.plugins import openai, silero, deepgram, cartesia

load_dotenv()

async def entrypoint(ctx: agents.JobContext):
    """Simple voice AI assistant entrypoint."""
    await ctx.connect()
    
    # Create voice session with explicit providers
    session = voice.AgentSession(
        stt=deepgram.STT(),
        llm=openai.LLM(model="gpt-4o-mini"),
        tts=cartesia.TTS(),
        vad=silero.VAD.load(),
    )
    
    # Create a simple voice agent
    agent = voice.Agent(
        instructions="You are a helpful voice AI assistant. Keep responses concise and friendly.",
    )
    
    # Start the session
    await session.start(agent, room=ctx.room)

if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))