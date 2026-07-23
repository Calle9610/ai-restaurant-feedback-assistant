"""Dummy tool used to exercise the tool-calling loop before real tools exist."""

SCHEMA = {
    "name": "echo",
    "description": "Echo back the given text. Used only to test the tool-calling loop.",
    "input_schema": {
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Text to echo back."},
        },
        "required": ["text"],
    },
}


def run(text: str) -> str:
    return text
