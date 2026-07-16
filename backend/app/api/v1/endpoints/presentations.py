import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, model_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.presentation import Presentation, PresentationStatus
from app.models.user import User
from app.schemas.presentation import PresentationRead
from app.services.documents.storage import get_storage_backend
from app.services.presentations import approval as _presentation_approval  # noqa: F401 — registers the approval handler
from app.tasks.queue import JobEnqueuer, get_job_queue

router = APIRouter()


class PresentationCreate(BaseModel):
    source_document_id: uuid.UUID | None = None
    source_text: str | None = None
    title: str | None = None
    instructions: str | None = None

    @model_validator(mode="after")
    def _validate_source(self) -> "PresentationCreate":
        if bool(self.source_document_id) == bool(self.source_text):
            raise ValueError("Provide exactly one of source_document_id or source_text")
        return self


@router.post("", response_model=PresentationRead, status_code=status.HTTP_201_CREATED)
async def create_presentation(
    payload: PresentationCreate,
    db: AsyncSession = Depends(get_db),
    queue: JobEnqueuer = Depends(get_job_queue),
    user: User = Depends(get_current_user),
) -> Presentation:
    presentation = Presentation(
        created_by_id=user.id,
        source_document_id=payload.source_document_id,
        source_text=payload.source_text,
        title=payload.title,
        instructions=payload.instructions,
    )
    db.add(presentation)
    await db.commit()
    await db.refresh(presentation, attribute_names=["created_at"])

    await queue.enqueue_job("generate_presentation", str(presentation.id))
    return presentation


@router.get("", response_model=list[PresentationRead])
async def list_presentations(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[Presentation]:
    result = await db.execute(select(Presentation).order_by(Presentation.created_at.desc()))
    return list(result.scalars().all())


@router.get("/{presentation_id}", response_model=PresentationRead)
async def get_presentation(
    presentation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Presentation:
    presentation = await db.get(Presentation, presentation_id)
    if presentation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Presentation not found")
    return presentation


@router.post("/{presentation_id}/regenerate", response_model=PresentationRead)
async def regenerate_presentation(
    presentation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    queue: JobEnqueuer = Depends(get_job_queue),
    _: User = Depends(get_current_user),
) -> Presentation:
    presentation = await db.get(Presentation, presentation_id)
    if presentation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Presentation not found")
    if presentation.status == PresentationStatus.generating:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already generating")

    presentation.status = PresentationStatus.draft
    presentation.failure_reason = None
    await db.commit()

    await queue.enqueue_job("generate_presentation", str(presentation.id))
    return presentation


@router.get("/{presentation_id}/download")
async def download_presentation(
    presentation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Response:
    presentation = await db.get(Presentation, presentation_id)
    if presentation is None or presentation.storage_key is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Presentation file not found")
    if presentation.status != PresentationStatus.approved:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This presentation must be approved before it can be downloaded",
        )

    storage = get_storage_backend()
    data = await storage.read(presentation.storage_key)
    filename = f"{presentation.title or 'presentation'}.pptx"
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
