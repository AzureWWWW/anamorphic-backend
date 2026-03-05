from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import jwt, JWTError
from models import User, Message, PublicKey
from sqlalchemy import select, insert
from database import SessionLocal
import json, time

router = APIRouter()
active_ws = {}

SECRET = "MY_SECRET"

@router.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()

    # ---- AUTHENTICATION ----
    token = ws.query_params.get("token")
    if not token:
        await ws.close(code=4401)
        return

    try:
        payload = jwt.decode(token, SECRET, algorithms=["HS256"])
        me_id = payload["user_id"]
    except JWTError:
        await ws.close(code=4401)
        return

    # fetch username
    async with SessionLocal() as db:
        user = await db.get(User, me_id)
        if not user:
            await ws.close(code=4401)
            return
        me_username = user.username

    active_ws[me_id] = ws


    try:
        # ---- MAIN LOOP ----
        while True:
            raw = await ws.receive_text()
            msg = json.loads(raw)

            mtype = msg.get("type")

            # ------- GET PUBKEY -------
            if mtype == "get_pubkey":
                target_username = msg["username"]
                async with SessionLocal() as db:
                    target = await db.scalar(
                        select(User).where(User.username == target_username)
                    )
                    if not target:
                        await ws.send_text(json.dumps({"type": "user_not_found"}))
                        continue

                    target_pubkey = await db.scalar(select(PublicKey).where(PublicKey.id==target.id))
                    if not target_pubkey.pubkey:
                        await ws.send_text(json.dumps({"type": "pubkey_not_found"}))
                        continue

                await ws.send_text(json.dumps({
                    "type": "pubkey",
                    "username": target_username,
                    "pubkey": target_pubkey.pubkey
                }))

            # ------- SEND CIPHERTEXT -------
            elif mtype == "ciphertext":
                target_username = msg["to"]

                async with SessionLocal() as db:
                    target = await db.scalar(
                        select(User).where(User.username == target_username)
                    )
                    if not target.active_status:
                        # store for offline
                        await db.execute(
                            insert(Message).values(
                                sender_id=me_id,
                                receiver_id=target.id,
                                body=msg["body"],
                                timestamp=int(time.time()),
                                delivered=False
                            )
                        )
                        await db.commit()

                # live push if online
                target_ws = active_ws.get(target.id)
                if target_ws:
                    await target_ws.send_text(raw)

    except WebSocketDisconnect:
        pass

    finally:
        active_ws.pop(me_id, None)
        