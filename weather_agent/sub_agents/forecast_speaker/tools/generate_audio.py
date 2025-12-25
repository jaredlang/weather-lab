import os
import time
from dotenv import load_dotenv

from google import genai
from google.genai import types
from google.adk.tools import ToolContext
import wave

from ....tools import get_current_timestamp

load_dotenv()

OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")

# Set up the wave file to save the output:
def _save_wave_file(file_path, pcm, channels=1, rate=24000, sample_width=2):
   with wave.open(file_path, "wb") as wf:
      wf.setnchannels(channels)
      wf.setsampwidth(sample_width)
      wf.setframerate(rate)
      wf.writeframes(pcm)


def generate_audio(tool_context: ToolContext, city_name: str, tone: str="cheerfully") -> dict[str, str]:
    # Generate docstring to explain the function
    """Generates an audio file from the given text content using text-to-speech synthesis.
        Args:
            tool_context (ToolContext): The tool context containing session state
            city_name (str): The name of the city for which the forecast is being made
            tone (str): The tone in which the content should be spoken. Default is "cheerfully".
        Return:
            dict[str, str]: A dictionary containing the status and file path of the generated audio file.
    """
    content = tool_context.state.get("FORECAST", "No forecast available at this moment. Please try again later.")

    client = genai.Client()

    response = client.models.generate_content(
        model=os.getenv("TTS_MODEL"),
        contents=f"Say in the {tone} tone: {content}",
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                    voice_name='Kore',
                    ),
                ),
            ),
        ),
    )

    data = response.candidates[0].content.parts[0].inline_data.data

    # expand the current timestamp to the file name
    forecast_timestamp = tool_context.state.get("FORECAST_TIMESTAMP", get_current_timestamp())
    file_name = f"forecast_audio_{forecast_timestamp}.wav"

    directory = os.path.join(OUTPUT_DIR, city_name)
    if not os.path.exists(directory):
        os.makedirs(directory)

    file_path = os.path.join(directory, file_name)
    _save_wave_file(file_path, data) # Saves the file to the specified directory

    return {"status": "success", "file_path": file_path}