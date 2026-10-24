from fastapi import APIRouter

from app.deps import Ai, CurrentStudent, Db
from app.schemas import ChatHistory, ChatIn, ChatReply
from app.services import chat

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatReply)
def post_chat(body: ChatIn, db: Db, ai: Ai, student: CurrentStudent) -> ChatReply:
    return chat.handle_chat(db, ai, student, body.session_id, body.message)


@router.get("/{session_id}", response_model=ChatHistory)
def get_chat(session_id: str, db: Db) -> ChatHistory:
    return chat.chat_history(db, session_id)
