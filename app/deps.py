from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from .database import get_db
from .models import User
from .security import parse_session


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get("session")
    if not token:
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    user_id = parse_session(token)
    if not user_id:
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    return user


def get_admin_user(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")
    return user