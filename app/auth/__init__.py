from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import User

def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Упрощенная авторизация через cookie user_id (для MVP)."""
    user_id = request.cookies.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Не авторизован")
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=401, detail="Пользователь не найден")
    return user