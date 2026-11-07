from typing import Annotated
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
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


@router.post("/stream")
async def stream(
    body: ChatRequest,
    request: Request,
    _current_user: Annotated[User, Depends(get_current_user)],
):
    authorization = request.headers.get("Authorization") or ""
    return StreamingResponse(
        # 传入异步生成器，由 StreamingResponse 逐项读取，这里不写 await。
        agent_service.stream_ask(body.question, body.history, authorization),
        # 这是 SSE 的标准 MIME 类型，告诉浏览器：这是一个持续不断的流
        media_type="text/event-stream",
        # 禁止缓存 防止代理服务器或浏览器缓存 SSE 响应
        # 禁用 Nginx缓冲 默认 Nginx 会缓冲响应，等到足够大才发送
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
