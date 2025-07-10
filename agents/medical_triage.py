import logging
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv
from livekit import agents
from livekit.agents import Agent, AgentSession, JobContext, WorkerOptions, cli, function_tool
from livekit.plugins import cartesia, deepgram, openai, silero
from livekit.plugins.openai import llm as openai_llm

logger = logging.getLogger("medical-office-triage")
logger.setLevel(logging.INFO)

load_dotenv()

@dataclass
class TriageUserData:
    """Stores data to be shared across agent handoffs"""
    patient_name: Optional[str] = None
    symptoms: Optional[str] = None
    urgency_level: Optional[str] = None
    department: Optional[str] = None


class TriageAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=(
                "You are a medical office triage agent. Your role is to:\n"
                "1. Greet patients warmly and professionally\n"
                "2. Ask for their name and reason for calling\n"
                "3. Collect basic information about symptoms and urgency\n"
                "4. Determine if they need medical support or billing assistance\n"
                "5. Transfer them to the appropriate department when ready\n\n"
                "Be empathetic, professional, and efficient. Always prioritize urgent medical concerns."
                "Ask one question at a time and wait for responses."
            ),
        )

    async def on_enter(self):
        # Greet the patient when they enter
        await self.session.generate_reply(
            instructions="Greet the patient warmly and ask for their name and the reason for their call today."
        )

    @function_tool
    async def collect_patient_info(
        self,
        patient_name: str,
        symptoms: str,
        urgency_level: str,
    ):
        """Called when basic patient information has been collected.
        
        Args:
            patient_name: The patient's name
            symptoms: Description of symptoms or reason for calling
            urgency_level: Assessment of urgency (low, medium, high, emergency)
        """
        userdata: TriageUserData = self.session.userdata
        userdata.patient_name = patient_name
        userdata.symptoms = symptoms
        userdata.urgency_level = urgency_level
        
        logger.info(f"Collected info for {patient_name}: {symptoms} (urgency: {urgency_level})")
        
        # Continue with triage assessment
        await self.session.generate_reply(
            instructions=(
                f"Thank the patient {patient_name} for the information. "
                "Based on their symptoms and urgency level, determine if they need "
                "medical support or billing assistance. Ask any clarifying questions needed."
            )
        )

    @function_tool
    async def transfer_to_support(self):
        """Transfer patient to medical support for clinical assistance."""
        userdata: TriageUserData = self.session.userdata
        userdata.department = "support"
        
        await self.session.say(
            "I'll transfer you to our Patient Support team who can help with your medical needs. "
            "Please hold on while I connect you."
        )
        
        return SupportAgent()

    @function_tool
    async def transfer_to_billing(self):
        """Transfer patient to billing department for insurance and payment questions."""
        userdata: TriageUserData = self.session.userdata
        userdata.department = "billing"
        
        await self.session.say(
            "I'll transfer you to our Medical Billing department who can assist with "
            "your insurance and payment questions. Please hold on while I connect you."
        )
        
        return BillingAgent()


class SupportAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=(
                "You are a medical support specialist. Your role is to:\n"
                "1. Help patients with medical service requests\n"
                "2. Assist with appointment scheduling\n"
                "3. Provide information about prescriptions and medications\n"
                "4. Answer general medical office questions\n"
                "5. Transfer to billing if payment/insurance questions arise\n"
                "6. Transfer back to triage if needed\n\n"
                "Be knowledgeable, helpful, and maintain patient confidentiality. "
                "You have access to the patient's information from triage."
            ),
        )

    async def on_enter(self):
        userdata: TriageUserData = self.session.userdata
        greeting = f"Hello {userdata.patient_name or 'there'}, I'm with Patient Support. "
        
        if userdata.symptoms:
            greeting += f"I see you're calling about {userdata.symptoms}. How can I help you today?"
        else:
            greeting += "How can I help you with your medical needs today?"
            
        await self.session.say(greeting)

    @function_tool
    async def transfer_to_triage(self):
        """Transfer back to triage if the patient needs different assistance."""
        await self.session.say(
            "I'll transfer you back to our triage team who can better direct your inquiry."
        )
        return TriageAgent()

    @function_tool
    async def transfer_to_billing(self):
        """Transfer to billing for insurance and payment questions."""
        await self.session.say(
            "I'll transfer you to our Medical Billing department for assistance with "
            "your insurance and payment questions."
        )
        return BillingAgent()


class BillingAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=(
                "You are a billing specialist. Your role is to:\n"
                "1. Help patients with insurance questions\n"
                "2. Assist with payment processing and billing inquiries\n"
                "3. Explain insurance coverage and benefits\n"
                "4. Handle billing disputes and claims\n"
                "5. Transfer to support for medical questions\n"
                "6. Transfer back to triage if needed\n\n"
                "Be patient, accurate, and helpful with financial matters. "
                "You have access to the patient's information from triage."
            ),
        )

    async def on_enter(self):
        userdata: TriageUserData = self.session.userdata
        greeting = f"Hello {userdata.patient_name or 'there'}, I'm with Medical Billing. "
        greeting += "How can I help you with your insurance or billing questions today?"
        
        await self.session.say(greeting)

    @function_tool
    async def transfer_to_triage(self):
        """Transfer back to triage for general inquiries."""
        await self.session.say(
            "I'll transfer you back to our triage team who can better direct your inquiry."
        )
        return TriageAgent()

    @function_tool
    async def transfer_to_support(self):
        """Transfer to medical support for clinical questions."""
        await self.session.say(
            "I'll transfer you to our Patient Support team who can help with "
            "your medical questions."
        )
        return SupportAgent()


async def entrypoint(ctx: agents.JobContext):
    """Main entrypoint for the medical triage agent system."""
    await ctx.connect()
    
    logger.info(f"Medical triage agent starting in room: {ctx.room.name}")
    
    # Initialize user data
    userdata = TriageUserData()
    
    # Create the agent session with voice pipeline
    session = AgentSession[TriageUserData](
        userdata=userdata,
        stt=deepgram.STT(model="nova-3-general"),
        llm=openai_llm.LLM(model="gpt-4o-mini"),  # Fast and cost-effective
        tts=cartesia.TTS(voice="8843adfb-77d3-455a-86f9-de0651555ec6"),  # Professional female voice
        vad=silero.VAD.load(),
    )
    
    # Start with the triage agent
    await session.start(
        agent=TriageAgent(),
        room=ctx.room,
    )


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))