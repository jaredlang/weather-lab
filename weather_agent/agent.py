import os 
from dotenv import load_dotenv
from google.adk.agents import Agent, SequentialAgent

from .sub_agents.forecast_writer.agent import forecast_writer_agent
from .sub_agents.forecast_speaker.agent import forecast_speaker_agent

from .tools import set_session_value, get_current_timestamp
from .forecast_cache import get_forecast_from_cache, cache_forecast, get_cache_stats

load_dotenv()

weather_studio_team = SequentialAgent(
    name="weather_studio_team",
    description="A team of agents that work together to provide current weather information.",
    sub_agents=[
        forecast_writer_agent, 
        forecast_speaker_agent
    ],
)

root_agent = Agent(
    name="weather_agent",
    model=os.getenv("MODEL"),
    instruction="""
    You are a weather information agent. Your task is to provide accurate and up-to-date weather forecast in a city.
    Use the sub-agents to gather and present the information effectively.

    - At the start of the conversation, let the user know you are here to provide current weather information.
      Ask for their city and the type of weather information they need.
    - After receiving the user's input, store the following data in the session: 
      * the city in the session with the key 'CITY'
      * the type of weather information in the session with the key 'WEATHER_TYPE'. If you are unsure, default to "current weather condition".
      * the current date and time in the session with the key 'FORECAST_TIMESTAMP'

    Steps to follow:
    - BEFORE delegating to sub-agents, use get_forecast_from_cache with the city name to check if a recent forecast exists.
    - If cached is True:
      * Store the forecast_text in session with key 'FORECAST'
      * Store the text_file_path in session with key 'FORECAST_TEXT_FILE'
      * Store the audio_file_path in session with key 'FORECAST_AUDIO'
      * Inform the user that you have their weather forecast ready
      * SKIP calling weather_studio_team entirely - you already have everything!
    - If cached is False:
      * Delegate the task of producing the weather forecast to the weather_studio_team.
      * After the sub-agents complete, use cache_forecast to cache the results for future requests.
        Get the FORECAST, FORECAST_TEXT_FILE, and FORECAST_AUDIO from session state to cache them.
    """,
    sub_agents=[weather_studio_team],
    tools=[get_current_timestamp, set_session_value, get_forecast_from_cache, cache_forecast, get_cache_stats],

)
