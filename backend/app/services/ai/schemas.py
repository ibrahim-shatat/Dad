"""Pydantic output models for Claude structured_call. One per AI-driven feature.

Feature schemas are added alongside their respective phase: Phase 1 adds
DocumentReviewResult, Phase 2 adds PresentationOutline, etc.
"""

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class RiskFlag(BaseModel):
    category: str = Field(
        description="Short category label, e.g. 'Liability', 'Ambiguous term', 'Missing clause'."
    )
    description: str = Field(
        description="Plain-English explanation of the risk, ambiguity, or contradiction found."
    )
    severity: Literal["low", "medium", "high"] = Field(
        description="How serious this issue is if left unaddressed."
    )


class DocumentReviewResult(BaseModel):
    executive_summary: str = Field(
        description="A concise executive summary of the document in plain English (3-6 sentences)."
    )
    risk_flags: list[RiskFlag] = Field(
        description="Specific risks, ambiguities, missing context, or contradictions found in the "
        "document. Empty list if none are found — do not invent risks."
    )
    suggested_rewrite: str = Field(
        description="Improved wording for the document's most problematic passages. Empty string "
        "if no rewrite is warranted."
    )


class SlideChart(BaseModel):
    categories: list[str] = Field(description="Category labels for the chart's x-axis.")
    values: list[float] = Field(description="Numeric values corresponding to each category, in order.")
    series_name: str = Field(description="Label for this data series, e.g. 'Revenue ($M)'.")


class SlideContent(BaseModel):
    layout: Literal["section_header", "bullets", "two_column", "chart"] = Field(
        description="Slide layout. Use 'bullets' for standard content slides, 'section_header' "
        "sparingly to separate major sections, 'two_column' to compare two things side by side, "
        "'chart' only when the source material has genuinely quantitative data worth visualizing."
    )
    title: str = Field(description="Slide title.")
    bullets: list[str] = Field(
        default_factory=list, description="Bullet points for a 'bullets' layout slide. 3-6 concise points, no paragraphs."
    )
    left_column: list[str] = Field(
        default_factory=list, description="Left column bullets, used only for a 'two_column' layout slide."
    )
    right_column: list[str] = Field(
        default_factory=list, description="Right column bullets, used only for a 'two_column' layout slide."
    )
    chart: SlideChart | None = Field(
        default=None, description="Chart data, present only for a 'chart' layout slide. Never invent numbers."
    )
    speaker_notes: str = Field(
        default="", description="Brief speaker notes expanding on what the presenter should say for this slide."
    )


class PresentationOutline(BaseModel):
    title: str = Field(description="Overall presentation title.")
    slides: list[SlideContent] = Field(
        description="Ordered content slides, not including the title slide itself (that's generated "
        "separately from the title). Aim for 6-12 slides total unless the source material clearly "
        "warrants more. The first slide should be an executive summary in 'bullets' layout."
    )


class ActionItemExtraction(BaseModel):
    description: str = Field(description="What needs to be done.")
    owner: str = Field(
        description="Who is responsible, by name as mentioned in the notes. Use 'Unassigned' if unclear."
    )
    due_date: date | None = Field(
        default=None,
        description="Due date in YYYY-MM-DD format if mentioned or clearly inferable from the notes, "
        "otherwise null. Never invent a date that isn't grounded in the source material.",
    )


class DecisionExtraction(BaseModel):
    description: str = Field(description="What was decided, or what still needs a decision.")
    decided_by: str = Field(
        description="Who made or owns this decision, by name as mentioned in the notes. Use 'Unclear' if not stated."
    )
    status: Literal["pending", "decided", "deferred"] = Field(
        description="Whether this has already been decided, is still pending a decision, or was explicitly deferred."
    )
    deadline: date | None = Field(
        default=None,
        description="Deadline for a pending decision, in YYYY-MM-DD format, if mentioned. Never invent a date.",
    )


class FollowUpEmailDraft(BaseModel):
    subject: str = Field(description="Email subject line for the follow-up.")
    body: str = Field(
        description="Email body summarizing the meeting and action items, in a professional, "
        "director-appropriate voice. Plain text, no markdown."
    )


class MeetingExtraction(BaseModel):
    summary: str = Field(description="Concise summary of the meeting in plain English (3-6 sentences).")
    action_items: list[ActionItemExtraction] = Field(
        description="Action items extracted from the notes. Empty list if none are present."
    )
    decisions: list[DecisionExtraction] = Field(
        description="Decisions extracted from the notes. Empty list if none are present."
    )
    follow_up_email: FollowUpEmailDraft | None = Field(
        default=None,
        description="A suggested follow-up email to attendees summarizing the meeting and action "
        "items. Omit (null) if a follow-up email isn't warranted for this content.",
    )


class EmailSummary(BaseModel):
    summary: str = Field(description="One or two sentence summary of the email's content and any ask.")
    urgency: Literal["low", "medium", "high"] = Field(
        description="How urgent/time-sensitive this email is for the director to act on."
    )


class ExecutiveBriefing(BaseModel):
    summary: str = Field(
        description="A concise executive briefing (3-6 sentences) in a calm, direct voice, "
        "written for a busy director starting their day. Lead with what matters most, name "
        "specifics from the provided data, and do not invent anything not present in it. If "
        "there is genuinely nothing pressing, say so plainly."
    )
    top_priorities: list[str] = Field(
        default_factory=list,
        description="Up to 3 short, action-oriented priorities for today, most important first. "
        "Each is a single imperative phrase (e.g. 'Approve the vendor contract email'). Empty "
        "list if nothing is pressing.",
    )


class EmailReplyDraft(BaseModel):
    subject: str = Field(description="Reply subject line, typically 'Re: ' plus the original subject.")
    body: str = Field(
        description="Reply body addressing the sender's points directly, in a professional, "
        "director-appropriate voice. Plain text, no markdown. Do not invent commitments, numbers, "
        "or facts not present in the original email or the director's instructions."
    )
