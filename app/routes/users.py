from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.user_service import UserService
from app.config import settings

from app.auth.jwt_handler import create_access_token, get_current_user
from app.models import User

router = APIRouter(prefix="/api")

@router.post("/onboard")
async def onboard_user(username: str, bot_name: str, pin: str = "0000", db: Session = Depends(get_db)):
    user = UserService.onboard_user(db, username, bot_name, pin)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized access. Invalid PIN.")
    
    # Create JWT Token
    access_token = create_access_token(data={"sub": str(user.id)})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id, 
        "username": user.username, 
        "bot_name": user.bot_name
    }
