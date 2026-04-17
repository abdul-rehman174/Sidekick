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
        "bot_name": user.bot_name,
        "persona_training": user.persona_training
    }

@router.post("/user/persona")
async def update_persona(persona_data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Professional DB Hardening: Limit training payload to 1500 chars to prevent DB bloat/token drain
    raw_persona = persona_data.get("persona_training", "")
    user.persona_training = raw_persona.strip()[:1500] if raw_persona else ""
    
    db.commit()
    db.refresh(user)
    return {"status": "success", "persona_training": user.persona_training}
