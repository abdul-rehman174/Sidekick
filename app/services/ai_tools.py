from typing import Any


def get_sidekick_tools() -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": "save_reminder",
                "description": "Save a task reminder for the user with a delay in minutes.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task": {
                            "type": "string",
                            "description": "The task to remember.",
                        },
                        "minutes": {
                            "type": "integer",
                            "description": "How many minutes from now the reminder should fire.",
                        },
                    },
                    "required": ["task", "minutes"],
                },
            },
        }
    ]
