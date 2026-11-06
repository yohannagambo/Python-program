from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.database import get_db
from backend.app.models import User
from backend.app.security import (
    create_access_token,
    hash_password,
    require_admin,
    verify_password,
)
from backend.app.services.audit_service import record_event

router = APIRouter(prefix="/auth", tags=["Authentication"])


class UserResponse(BaseModel):
    id: int
    email: str
    role: str
    is_active: bool

    model_config = {"from_attributes": True}


def ensure_admin(db: Session):
    admin = db.query(User).filter(
        User.email == settings.admin_email.lower()
    ).first()

    if not admin:
        admin = User(
            email=settings.admin_email.lower(),
            password_hash=hash_password(settings.admin_password),
            role="admin",
            is_active=True,
        )
        db.add(admin)
        db.commit()


@router.post("/login")
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    email = form.username.lower().strip()

    user = db.query(User).filter(User.email == email).first()

    if not user or not user.is_active or not verify_password(
        form.password, user.password_hash
    ):
        record_event(
            db,
            actor=email or "unknown",
            action="login",
            outcome="failure",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    token = create_access_token(user.email, user.role)

    record_event(db, user.email, "login")

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in_minutes": settings.access_token_minutes,
    }


@router.get("/me", response_model=UserResponse)
def current_user(user: User = Depends(require_admin)):
    return user
