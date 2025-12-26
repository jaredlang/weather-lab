import os 
from dotenv import load_dotenv
from google.adk.agents import Agent

from .tools.generate_audio import generate_audio
from ...tools import set_session_value

load_dotenv()

forecast_speaker_agent = Agent(
    name="forecast_speaker_agent",
    model=os.getenv("MODEL"),
    instruction= f"""You are a professional weather news anchor. Based on the weather text in {{FORECAST_TEXT}} for {{CITY}},
        You should follow these steps:
         1. Read the weather forecast text stored in the session with the key 'FORECAST_TEXT'.
         2. Understand the forecast content and select an appropriate tone to make the announcement engaging and suitable for the weather conditions.
         3. Convert the text forecast into an engaging audio announcement using the generate_audio tool.
         4. Store the generated audio file path in the session with the key 'FORECAST_AUDIO'.
        """,
    tools=[generate_audio, set_session_value],
)