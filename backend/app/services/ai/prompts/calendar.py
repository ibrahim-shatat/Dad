"""Prompts for calendar features: pre-meeting prep briefs and post-meeting follow-up emails."""

PREP_SYSTEM_PROMPT = """You are an executive assistant preparing a company director for an \
upcoming meeting. Using only the event details provided (title, description, attendees, time, \
location), write a focused prep brief: what the meeting is about, the points the director should \
be ready to make, sharp questions worth asking, and anything to prepare beforehand.

Be concise and practical. Never invent facts, attendees, or agenda items that aren't supported \
by the provided details. If the event is sparse, keep the brief short rather than padding it.
"""

FOLLOW_UP_SYSTEM_PROMPT = """You are an executive assistant drafting a brief, professional \
follow-up email after a meeting, written in the director's voice. Summarize what was covered and \
list any agreed next steps. Plain text, no markdown. Do not invent commitments, decisions, or \
details that aren't supported by the event information provided.
"""


def build_prep_prompt(
    *,
    title: str,
    description: str | None,
    location: str | None,
    start_time: str,
    organizer: str | None,
    attendees: list[str],
) -> str:
    lines = [f"Title: {title}", f"When: {start_time}"]
    if location:
        lines.append(f"Location: {location}")
    if organizer:
        lines.append(f"Organizer: {organizer}")
    if attendees:
        lines.append(f"Attendees: {', '.join(attendees)}")
    if description:
        lines.append(f"Description/agenda:\n{description}")
    return "Prepare a prep brief for this meeting:\n\n" + "\n".join(lines)


def build_follow_up_prompt(
    *,
    title: str,
    description: str | None,
    attendees: list[str],
) -> str:
    lines = [f"Meeting: {title}"]
    if attendees:
        lines.append(f"Attendees: {', '.join(attendees)}")
    if description:
        lines.append(f"What it covered:\n{description}")
    return (
        "Draft a follow-up email to the attendees for this meeting:\n\n" + "\n".join(lines)
    )
