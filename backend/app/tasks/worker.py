from arq.connections import RedisSettings
from arq.cron import cron

from app.core.config import settings
from app.tasks.jobs import (
    draft_email_reply,
    draft_event_follow_up,
    extract_document_text,
    generate_event_prep,
    generate_presentation,
    process_meeting,
    review_document,
    sync_all_calendars,
    sync_all_email_accounts,
    sync_calendar_account,
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
        sync_calendar_account,
        sync_all_calendars,
        generate_event_prep,
        draft_event_follow_up,
    ]
    cron_jobs = [
        cron(sync_all_email_accounts, minute={0, 15, 30, 45}),
        cron(sync_all_calendars, minute={5, 35}),
    ]
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
