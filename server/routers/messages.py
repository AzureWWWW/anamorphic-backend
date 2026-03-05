from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import time

from deps import get_db, get_current_user
from models import Message, User

router = APIRouter()

class HistoryIn(BaseModel):
    with_user: str
    limit: int = 50
    before_ts: int | None = None

@router.post("/history")
async def history(p: HistoryIn, db: AsyncSession = Depends(get_db), me: User = Depends(get_current_user)):
    peer = await db.scalar(select(User).where(User.username == p.with_user))
    if not peer:
        return {"items": []}
    cutoff = p.before_ts or int(time.time())
    q = (
        select(Message)
        .where(
            (
                (Message.sender_id == me.id) & (Message.receiver_id == peer.id)
            ) | (
                (Message.sender_id == peer.id) & (Message.receiver_id == me.id)
            ),
            Message.timestamp < cutoff
        )
        .order_by(Message.timestamp.desc())
        .limit(p.limit)
    )
    rows = (await db.scalars(q)).all()
    items = [
        {
            "type": "ciphertext",
            "from": r.sender_id,
            "to": r.receiver_id,
            "timestamp": r.timestamp,
            "body": r.body
        }
        for r in rows
    ]
    return {"items": items}