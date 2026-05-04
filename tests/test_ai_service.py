from types import SimpleNamespace

from app.services.ai_service import AIService


def make_user(**overrides):
    base = dict(
        id=1,
        username="test_user",
        persona_name="Sidekick",
        behavior_profile=None,
        system_instruction=None,
        chat_summary=None,
        summary_message_count=0,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def test_build_messages_bare_persona():
    user = make_user()
    messages = AIService._build_messages(user, history=[], user_message="hello")

    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert "Sidekick" in messages[0]["content"]
    assert "test_user" in messages[0]["content"]
    assert messages[1] == {"role": "user", "content": "hello"}


def test_build_messages_injects_behavior_profile_and_instruction():
    user = make_user(
        persona_name="Nova",
        behavior_profile="hey bae\nhru?? miss u sm",
        system_instruction="respond in Roman Urdu",
    )
    messages = AIService._build_messages(user, history=[], user_message="sup")

    system_content = messages[0]["content"]
    assert "Nova" in system_content
    assert "hey bae" in system_content
    assert "VOICE PROFILE" in system_content
    assert "respond in Roman Urdu" in system_content
    assert "narration" in system_content.lower()
    assert "<function=" in system_content


def test_scrub_tool_leaks_removes_function_tags():
    text = "Hm reminder bhej rhi thi yr <function=save_reminder>{\"task\":\"x\",\"minutes\":30}</function>"
    cleaned = AIService._scrub_tool_leaks(text)
    assert "<function=" not in cleaned
    assert "save_reminder" not in cleaned
    assert cleaned == "Hm reminder bhej rhi thi yr"


def test_scrub_tool_leaks_removes_python_tag():
    text = "ok <|python_tag|>save_reminder(task=\"x\")"
    cleaned = AIService._scrub_tool_leaks(text)
    assert "python_tag" not in cleaned
    assert cleaned.startswith("ok")


def test_scrub_tool_leaks_preserves_plain_text():
    text = "ya kia kh rhi ho ?"
    assert AIService._scrub_tool_leaks(text) == text


def test_scrub_tool_leaks_strips_think_blocks():
    text = "<think>Okay let me figure out a flirty reply.\nMaybe I should tease him.</think>\nhlo back :) busy with what?"
    cleaned = AIService._scrub_tool_leaks(text)
    assert "<think>" not in cleaned
    assert "Okay let me" not in cleaned
    assert cleaned == "hlo back :) busy with what?"


def test_build_messages_includes_history_in_order():
    user = make_user()
    history = [
        SimpleNamespace(role="model", content="reply-2"),
        SimpleNamespace(role="user", content="msg-2"),
        SimpleNamespace(role="model", content="reply-1"),
        SimpleNamespace(role="user", content="msg-1"),
    ]
    messages = AIService._build_messages(user, history=history, user_message="now")

    roles_contents = [(m["role"], m["content"]) for m in messages[1:-1]]
    assert roles_contents == [
        ("user", "msg-1"),
        ("assistant", "reply-1"),
        ("user", "msg-2"),
        ("assistant", "reply-2"),
    ]
    assert messages[-1] == {"role": "user", "content": "now"}


def test_build_messages_omits_behavior_section_when_empty():
    user = make_user(behavior_profile="", system_instruction="")
    messages = AIService._build_messages(user, history=[], user_message="hi")

    system_content = messages[0]["content"]
    assert "VOICE PROFILE" not in system_content
    assert "ADDITIONAL USER INSTRUCTIONS" not in system_content
    assert "PREVIOUS CONTEXT" not in system_content


def test_build_messages_injects_chat_summary():
    user = make_user(chat_summary="user said his name is faizan and likes mango shake")
    messages = AIService._build_messages(user, history=[], user_message="hi")

    system_content = messages[0]["content"]
    assert "PREVIOUS CONTEXT" in system_content
    assert "mango shake" in system_content
