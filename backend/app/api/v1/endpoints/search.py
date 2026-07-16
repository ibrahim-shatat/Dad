from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.search import ChatRequest, ChatResponse, ChatSourceRead, SearchResultRead
from app.services.ai.client import claude_client
from app.services.ai.prompts import chat as chat_prompts
from app.services.ai.schemas import ChatAnswer
from app.services.search import service as search_service

router = APIRouter()


@router.get("", response_model=list[SearchResultRead])
async def search(
    q: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[SearchResultRead]:
    results = await search_service.search_workspace(db, user, q)
    return [SearchResultRead(**vars(r)) for r in results]


@router.post("/chat", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ChatResponse:
    context = await search_service.assemble_workspace_context(db, user, payload.question)
    try:
        answer: ChatAnswer = await claude_client.structured_call(
            system=chat_prompts.SYSTEM_PROMPT,
            user=chat_prompts.build_user_prompt(payload.question, context),
            output_model=ChatAnswer,
            model=settings.claude_model_smart,
            max_tokens=1024,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"The assistant could not answer right now: {exc}",
        )
    return ChatResponse(
        answer=answer.answer,
        sources=[ChatSourceRead(label=s.label, link=s.link) for s in answer.sources],
    )
