from google.adk.tools import ToolContext

def set_session_value(tool_context: ToolContext, key: str, value: str):
    """Set a value in the tool_context's states dictionary."""
    tool_context.state[key] = value

    return {"status": "success", "message": f"Set {key} to {value} in session."}

def get_current_timestamp():
    """Get the current timestamp."""
    from datetime import datetime

    current_time = datetime.now().strftime("%Y-%m-%d_%H%M%S")

    return current_time
