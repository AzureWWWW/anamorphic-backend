from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt
from datetime import datetime, timedelta, timezone

from database import SessionLocal, settings
from models import User, PublicKey
from encryption_db import hash_password, verify_password

router = APIRouter()

async def get_db():
    async with SessionLocal() as session:
        yield session

def create_token(sub: str):
    payload = {"sub": sub, "exp": datetime.now(timezone.utc) + timedelta(days=7)}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALG)

@router.post("/signup")
async def signup(username: str, password: str, db: AsyncSession = Depends(get_db)):
    exists = await db.scalar(select(User).where(User.username == username))
    if exists:
        raise HTTPException(400, "username_taken")
    user = User(username=username, password_hash=hash_password(password))
    db.add(user)
    await db.commit()
    return {"message": "User signup successfully"}


@router.post("/login")
async def login(form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = await db.scalar(select(User).where(User.username == form.username))
    if not user or not verify_password(form.password,user.password_hash):
        raise HTTPException(401, "invalid_credentials")
    
    # set active_status when login
    user.active_status = True
    await db.commit()

    token = create_token(str(user.id))
    return {"access_token": token, "token_type": "bearer"}

@router.post("/logout")
async def logout():
    pass