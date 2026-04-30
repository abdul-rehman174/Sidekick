from typing import Optional

from pydantic import BaseModel, Field, constr


PinStr = constr(pattern=r"^\d{4}$")
UsernameStr = constr(strip_whitespace=True, min_length=1, max_length=40)


class OnboardRequest(BaseModel):
    username: UsernameStr
    pin: PinStr
    persona_name: str = Field(default="Sidekick", max_length=40, min_length=1)


class OnboardResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str
    persona_name: str


class PersonaResponse(BaseModel):
    persona_name: str
    behavior_profile: Optional[str] = None
    system_instruction: Optional[str] = None


class PersonaUpdateRequest(BaseModel):
    persona_name: Optional[str] = Field(default=None, max_length=40, min_length=1)
    behavior_profile: Optional[str] = Field(default=None, max_length=50000)
    system_instruction: Optional[str] = Field(default=None, max_length=4000)


class CompressPersonaRequest(BaseModel):
    raw_chat: str = Field(..., min_length=20, max_length=50000)


class CompressPersonaResponse(BaseModel):
    compressed: str
    # TOKEN_COUNTER: remove when done testing
    tokens: Optional[dict] = None


class ChatRequest(BaseModel):
    user_message: str = Field(..., min_length=1, max_length=4000)
