from typing import Annotated
from fastapi import APIRouter, Depends, Request

from app.common.response import Response
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.chat import ChatRequest
from app.services import agent_service

router = APIRouter(prefix="/chat", tags=["AI 对话"])


@router.post("/ask")
async def ask(
    body: ChatRequest,
    request: Request,
    _current_user: Annotated[User, Depends(get_current_user)],
):
    """接收问题和历史消息，返回完整的助手回答"""
    authorization = request.headers.get("Authorization") or ""
    data = await agent_service.ask(body.question, body.history, authorization)
    return Response.success(data=data)
