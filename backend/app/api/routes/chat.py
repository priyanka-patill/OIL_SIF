from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services.ai.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["AI Safety Chat"])


class ChatMessageRequest(BaseModel):
    message: str
    report_id: Optional[str] = None
    dataset_id: Optional[str] = None


class ChatMessageResponse(BaseModel):
    reply: str
    suggested_actions: List[str] = []
    relevant_reports: List[Dict[str, Any]] = []
    category: str = "GENERAL"


@router.post("", response_model=ChatMessageResponse)
def handle_safety_chat(
    req: ChatMessageRequest,
    db: Session = Depends(get_db)
):
    """
    AI Safety Intelligence Assistant grounded in actual database records.
    Never fabricates numbers. Handles database queries, natural language filtering,
    and report-specific contextual QA.
    """
    result = ChatService.process_chat_message(
        db=db,
        message=req.message,
        report_id=req.report_id,
        dataset_id=req.dataset_id
    )
    return ChatMessageResponse(**result)
