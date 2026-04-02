from typing import List, Dict, Any

def get_sidekick_tools() -> List[Dict[str, Any]]:
    """
    Returns the JSON-compatible tool schema for the Sidekick's capabilities.
    
    This schema follows the OpenAI/Groq tool specification for function calling.
    
    Returns:
        A list of dictionary objects defining the available tools (e.g., save_reminder).
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "save_reminder",
                "description": "Store a task reminder for the user with an automated delay.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task": {
                            "type": "string", 
                            "description": "The specific task to be remembered."
                        },
                        "minutes": {
                            "type": "string", 
                            "description": "Countdown interval in minutes (numeric string, e.g., '30')."
                        }
                    },
                    "required": ["task", "minutes"]
                }
            }
        }
    ]
