"""Registers the real approval handler for presentation exports. Imported (for its side effect)
from the presentations endpoint module so registration happens at app startup.
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.approval import ApprovalItemType
from app.models.presentation import Presentation, PresentationStatus
from app.services.approvals.service import register_handler


class PresentationExportHandler:
    async def on_approve(self, db: AsyncSession, reference_id: uuid.UUID) -> None:
        presentation = await db.get(Presentation, reference_id)
        if presentation is not None:
            presentation.status = PresentationStatus.approved

    async def on_reject(self, db: AsyncSession, reference_id: uuid.UUID) -> None:
        presentation = await db.get(Presentation, reference_id)
        if presentation is not None:
            presentation.status = PresentationStatus.draft


register_handler(ApprovalItemType.presentation_export, PresentationExportHandler())
