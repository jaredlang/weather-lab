import chainlit as cl
import vertexai
from vertexai import agent_engines
from dotenv import load_dotenv

load_dotenv()

# project_id = "your-project-id"
# location = "us-central1"
# vertexai.init(project=project_id, location=location)

agent = agent_engines.get("projects/951067725786/locations/us-central1/reasoningEngines/5857804327627784192")

@cl.set_starters
async def set_starters():
    """Initialize the chat session with starter prompts."""
    return [
        cl.Starter(
            label="🌤️ Primo Weather Station",
            message="What's the current weather in New York?",
            icon="/public/weather-icon.svg"
        ),
        cl.Starter(
            label="🌍 Global Weather",
            message="What's the weather like in Tokyo?",
            icon="/public/weather-icon.svg"
        ),
        cl.Starter(
            label="🌡️ Temperature Check",
            message="How hot is it in Dubai right now?",
            icon="/public/weather-icon.svg"
        ),
    ]

@cl.on_chat_start
async def on_chat_start():
    """Initialize the chat session and send welcome message."""
    print("A new chat session has started.")
    user_id = "user_123"
    print(f"User ID: {user_id}")

    session_details = agent.create_session(user_id=user_id)
    cl.user_session.set("user_id", user_id)
    cl.user_session.set("session_id", session_details["id"])
    cl.user_session.set("message_history", [{
        "role": "system",
        "content": "You are a helpful assistant that provides current weather information."
    }])

    # Send welcome message to match Streamlit UI
    await cl.Message(
        content="**🌤️ Primo Weather Station**\n\nWelcome to Primo Weather Station! Ask me about the weather in any city.",
        author="system"
    ).send()

@cl.on_message
async def main(message: cl.Message):
    message_history = cl.user_session.get("message_history")
    message_history.append({"role": "user", "content": message})

    events = agent.stream_query(
        user_id=cl.user_session.get("user_id" ),
        session_id=cl.user_session.get("session_id"),
        message=message.content,
    )

    msg = cl.Message(content="")

    # Stream the response from the agent to the user
    for event in events:
        print (event)
        for part in event["content"]["parts"]:
            print (part)
            if "text" in part:
                await msg.stream_token(part["text"])

    message_history.append({"role": "assistant", "content": msg.content})
    await msg.update()
