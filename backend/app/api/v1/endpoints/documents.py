import uuid

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.document import Document
from app.models.user import User
from app.schemas.document import DocumentRead
from app.services.documents.storage import get_storage_backend
from app.tasks.queue import JobEnqueuer, get_job_queue

router = APIRouter()

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/plain",
}


@router.post("", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile,
    instructions: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
    queue: JobEnqueuer = Depends(get_job_queue),
    user: User = Depends(get_current_user),
) -> Document:
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {file.content_type}",
        )

    data = await file.read()
    storage = get_storage_backend()
    storage_key = await storage.save(data, file.filename or "document")

    document = Document(
        uploaded_by_id=user.id,
        filename=file.filename or "document",
        storage_key=storage_key,
        mime_type=file.content_type,
        file_size=len(data),
        instructions=instructions or None,
    )
    # Set explicitly (rather than leaving unset) so the relationship is already
    # populated in-memory — accessing an unset relationship later during response
    # serialization would trigger an async lazy-load, which SQLAlchemy can't do
    # outside an awaited context.
    document.review = None
    db.add(document)
    await db.commit()
    await db.refresh(document, attribute_names=["created_at"])

    await queue.enqueue_job("extract_document_text", str(document.id))
    return document


@router.get("", response_model=list[DocumentRead])
async def list_documents(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[Document]:
    result = await db.execute(
        select(Document)
        .options(selectinload(Document.review))
        .order_by(Document.created_at.desc())
    )
    return list(result.scalars().all())


async def _get_document_with_review(db: AsyncSession, document_id: uuid.UUID) -> Document:
    result = await db.execute(
        select(Document).options(selectinload(Document.review)).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return document


@router.get("/{document_id}", response_model=DocumentRead)
async def get_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Document:
    return await _get_document_with_review(db, document_id)


@router.post("/{document_id}/review/ack", response_model=DocumentRead)
async def acknowledge_review_disclaimer(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Document:
    document = await _get_document_with_review(db, document_id)
    if document.review is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No review yet for this document")

    document.review.disclaimer_ack = True
    await db.commit()
    return document
