import streamlit as st
import vertexai
from vertexai import agent_engines
from dotenv import load_dotenv
import json
import os
from pathlib import Path

load_dotenv()

# project_id = "your-project-id"
# location = "us-central1"
# vertexai.init(project=project_id, location=location)

# Initialize the agent
AGENT_ENGINE_ID = os.getenv("AGENT_ENGINE_ID")
agent = agent_engines.get(AGENT_ENGINE_ID)

# Chat history file path
HISTORY_DIR = Path(__file__).parent / "chat_history"
HISTORY_FILE = HISTORY_DIR / "chat_history.json"

def load_chat_history():
    """Load chat history from file."""
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, 'r') as f:
                data = json.load(f)
                return data.get("message_history", []), data.get("session_id")
        except Exception as e:
            print(f"Error loading chat history: {e}")
    return None, None

def save_chat_history(message_history, session_id):
    """Save chat history to file."""
    try:
        HISTORY_DIR.mkdir(exist_ok=True)
        with open(HISTORY_FILE, 'w') as f:
            json.dump({
                "message_history": message_history,
                "session_id": session_id
            }, f, indent=2)
    except Exception as e:
        print(f"Error saving chat history: {e}")

# Page configuration
st.set_page_config(
    page_title="Primo Weather Station",
    page_icon="🌤️",
    layout="centered"
)

# Initialize session state
if "user_id" not in st.session_state:
    st.session_state.user_id = "user_123"

    # Try to load existing chat history
    loaded_history, loaded_session_id = load_chat_history()

    if loaded_history and loaded_session_id:
        # Restore previous session
        st.session_state.session_id = loaded_session_id
        st.session_state.message_history = loaded_history
        print(f"Restored session. User ID: {st.session_state.user_id}, Session ID: {loaded_session_id}")
    else:
        # Create new session
        session_details = agent.create_session(user_id=st.session_state.user_id)
        st.session_state.session_id = session_details["id"]
        st.session_state.message_history = [{
            "role": "system",
            "content": "You are a helpful assistant that provides current weather information."
        }]
        print(f"New session started. User ID: {st.session_state.user_id}, Session ID: {st.session_state.session_id}")
        # Save initial state
        save_chat_history(st.session_state.message_history, st.session_state.session_id)

# Header with title and clear button
col1, col2 = st.columns([4, 1])
with col1:
    st.title("🌤️ Primo Weather Station")
    st.markdown("Welcome to Primo Weather Station! Ask me about the weather in any city.")
with col2:
    st.write("")  # Spacing
    if st.button("🗑️ Clear", help="Clear all chat history", use_container_width=True):
        st.session_state.message_history = [{
            "role": "system",
            "content": "You are a helpful assistant that provides current weather information."
        }]
        # Create a new session
        session_details = agent.create_session(user_id=st.session_state.user_id)
        st.session_state.session_id = session_details["id"]
        # Save cleared history
        save_chat_history(st.session_state.message_history, st.session_state.session_id)
        st.rerun()

st.divider()

# Display chat messages from history
for message in st.session_state.message_history:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("What's the current weather in New York?"):
    # Add user message to chat history
    st.session_state.message_history.append({"role": "user", "content": prompt})

    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display assistant response with streaming
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        # Stream the response from the agent
        events = agent.stream_query(
            user_id=st.session_state.user_id,
            session_id=st.session_state.session_id,
            message=prompt,
        )

        for event in events:
            print("*** EVENT *** ", event)
            for part in event["content"]["parts"]:
                print(">>> PART >>> ", part)
                if "text" in part:
                    full_response += part["text"]
                    message_placeholder.markdown(full_response + "▌")

        message_placeholder.markdown(full_response)

    # Add assistant response to chat history
    st.session_state.message_history.append({"role": "assistant", "content": full_response})

    # Save chat history to file
    save_chat_history(st.session_state.message_history, st.session_state.session_id)
