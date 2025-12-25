import os 
from dotenv import load_dotenv
from google.adk.agents import Agent, SequentialAgent

from .sub_agents.forecast_writer.agent import forecast_writer_agent
from .sub_agents.forecast_speaker.agent import forecast_speaker_agent

from .tools import set_session_value, get_current_timestamp

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
    - After receiving the user's input, store the city in the session with the key 'CITY' 
      and the type of weather information in the session with the key 'WEATHER_TYPE'
      and set the current time and date in the session with the key 'FORECAST_TIMESTAMP'.
    - Delegate the task of producing the weather forecast to the weather_studio_team.
    """,
    sub_agents=[weather_studio_team],
    tools=[get_current_timestamp, set_session_value],
    
)

# root_agent = Agent(
#     name="weather_agent",
#     model=os.getenv("MODEL"),
#     instruction="""
#     You are a weather information agent. Your task is to provide accurate and up-to-date weather forecast in a city. 
#     Use the sub-agents to gather and present the information effectively.

#     - At the start of the conversation, let the user know you are here to provide current weather information. 
#       Ask for their city and the type of weather information they need.
#     - After receiving the user's input, store the city in the session with the key 'CITY'.
#     - Delegate the task of fetching and writing the weather forecast to the forecast_writer_agent.
#     - if an audio output is requested, delegate the task of generating audio from the forecast to the forecast_speaker_agent.
#     """,
#     sub_agents=[forecast_writer_agent, forecast_speaker_agent],
#     tools=[set_session_value],
    
# )