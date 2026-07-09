from arq.connections import RedisSettings
from arq.cron import cron

from app.core.config import settings
from app.tasks.jobs import (
    draft_email_reply,
    extract_document_text,
    generate_presentation,
    process_meeting,
    review_document,
    sync_all_email_accounts,
    sync_email_account,
)


class WorkerSettings:
    functions = [
        extract_document_text,
        review_document,
        generate_presentation,
        process_meeting,
        sync_email_account,
        draft_email_reply,
        sync_all_email_accounts,
    ]
    cron_jobs = [cron(sync_all_email_accounts, minute={0, 15, 30, 45})]
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
