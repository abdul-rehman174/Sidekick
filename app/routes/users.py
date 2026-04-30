from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt_handler import create_access_token, get_current_user
from app.database import get_db
from app.models import User
from app.schemas import (
    AuthResponse,
    CompressPersonaRequest,
    CompressPersonaResponse,
    LoginRequest,
    PersonaResponse,
    PersonaUpdateRequest,
    RegisterRequest,
)
from app.services.ai_service import AIService
from app.services.user_service import UserService

router = APIRouter(prefix="/api")


def _auth_response(user: User) -> AuthResponse:
    return AuthResponse(
        access_token=create_access_token({"sub": str(user.id)}),
        user_id=user.id,
        username=user.username,
        persona_name=user.persona_name,
    )


@router.post("/register", response_model=AuthResponse, status_code=201)
async def register_user(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    user = await UserService.register_user(
        db, payload.username, payload.password, payload.persona_name
    )
    return _auth_response(user)


@router.post("/login", response_model=AuthResponse)
async def login_user(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await UserService.authenticate_user(db, payload.username, payload.password)
    return _auth_response(user)


@router.get("/persona", response_model=PersonaResponse)
async def get_persona(current_user: User = Depends(get_current_user)):
    return PersonaResponse(
        persona_name=current_user.persona_name,
        behavior_profile=current_user.behavior_profile,
        system_instruction=current_user.system_instruction,
    )


@router.put("/persona", response_model=PersonaResponse)
async def update_persona(
    payload: PersonaUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = await UserService.update_persona(
        db,
        current_user,
        persona_name=payload.persona_name,
        behavior_profile=payload.behavior_profile,
        system_instruction=payload.system_instruction,
    )
    return PersonaResponse(
        persona_name=user.persona_name,
        behavior_profile=user.behavior_profile,
        system_instruction=user.system_instruction,
    )


@router.post("/persona/compress", response_model=CompressPersonaResponse)
async def compress_persona(
    payload: CompressPersonaRequest,
    current_user: User = Depends(get_current_user),
):
    result = await AIService.compress_behavior_profile(
        raw_chat=payload.raw_chat,
        target=current_user.persona_name,
    )
    return CompressPersonaResponse(compressed=result["compressed"], tokens=result["tokens"])
