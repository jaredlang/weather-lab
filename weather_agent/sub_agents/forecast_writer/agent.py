import os 
import time
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.tools import ToolContext

from .tools.get_current_weather import get_current_weather
from ...tools import set_session_value, get_current_timestamp

load_dotenv()

OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")

def write_text_file(tool_context: ToolContext, directory: str) -> dict[str, str]:
    content = tool_context.state.get("FORECAST", "No forecast available at this moment. Please try again later.")
    if not os.path.exists(directory):
        os.makedirs(directory)

    # expand the current timestamp to the file name
    forecast_timestamp = tool_context.state.get("FORECAST_TIMESTAMP", get_current_timestamp())
    file_name = f"forecast_text_{forecast_timestamp}.txt"

    directory = os.path.join(OUTPUT_DIR, directory)
    if not os.path.exists(directory):
        os.makedirs(directory)

    file_path = os.path.join(directory, file_name)
    with open(file_path, "w") as f:
        f.write(content)

    return {"status": "success", "file_path": file_path}

forecast_writer_agent = Agent(
    name="forecast_writer_agent",
    model=os.getenv("MODEL"),
    instruction= f"""You are a professional weather forecaster. Based on the following current weather data for {{CITY}},
        write a friendly and engaging weather forecast announcement. 
        The announcement should be:
        - Conversational and easy to understand
        - About 3-4 sentences long
        - Include practical advice (e.g., "bring an umbrella", "dress warmly")
        - Suitable for text-to-speech conversion

        Steps to follow:
        1. Use the get_current_weather tool to obtain the current weather data.
        2. Use the set_session_value tool to store the generated forecast in the session with the key 'FORECAST'.
        3. Use the write_file tool to save the forecast to a text file in the directory named after the city.

        Write only the announcement text, nothing else.""",
    
    tools=[get_current_weather, set_session_value, write_text_file],
)