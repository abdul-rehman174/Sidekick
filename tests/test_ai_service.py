import pytest
from app.services.ai_service import AIService
from app.exceptions import AIInferenceError
from app.models import User

class DummyUser:
    def __init__(self, username, bot_name, persona_training):
        self.username = username
        self.bot_name = bot_name
        self.persona_training = persona_training

@pytest.fixture
def mock_user():
    return DummyUser("test_user", "Sidekick", "Be extremely sassy.")

def test_scrub_ai_refusals(mock_user):
    # Test that refusal patterns are swapped
    response = "I'm sorry, I can't do that right now."
    scrubbed = AIService.scrub_ai_refusals(response, mock_user)
    assert response != scrubbed
    assert "🫦" in scrubbed or "😘" in scrubbed or "😏" in scrubbed or "✨" in scrubbed

def test_build_prompt_structure(mock_user):
    # Test that the prompt injects the variables correctly
    history = []
    messages = AIService._build_prompt(mock_user, history, "hey set a timer")
    
    # Needs 2 messages: system, and user
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert mock_user.bot_name in messages[0]["content"]
    assert mock_user.username in messages[0]["content"]
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == "hey set a timer"
