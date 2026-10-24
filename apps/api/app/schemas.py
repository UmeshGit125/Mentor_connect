from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, StringConstraints

Seniority = Literal["Mid-career", "Senior"]
Quality = Literal["Excellent", "Good"]
BookingStatus = Literal["confirmed", "completed", "no_show", "cancelled"]
WriteupStatus = Literal["none", "notes_received", "ready"]
ReplyKind = Literal["clarify", "matches", "no_match", "redirect"]


class Tools(BaseModel):
    tableau: bool | None = None
    hubspot: bool | None = None
    google_analytics: bool | None = None
    jira: bool | None = None
    excel: bool | None = None
    mixpanel: bool | None = None


class PublicMentor(BaseModel):
    """Mentor fields safe to show. Email, phone and LinkedIn are never part of this type."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    city: str | None = None
    domain: str
    company: str | None = None
    sector: str | None = None
    sectors: list[str] = []
    roles: list[str] = []
    seniority: Seniority | None = None
    built_ai: bool | None = None
    ai_tools: list[str] = []
    tools: Tools = Tools()
    quality: Quality | None = None
    activities: int | None = None


class Reason(BaseModel):
    field: str
    value: str
    text: str


class Match(BaseModel):
    mentor: PublicMentor
    reasons: list[Reason]


class Need(BaseModel):
    summary: str
    domains: list[str] = []
    sectors: list[str] = []
    tools: list[str] = []
    wants_ai: bool = False


class ChatReply(BaseModel):
    session_id: str
    kind: ReplyKind
    message: str
    matches: list[Match] = []
    need: Need | None = None


class ChatMessage(BaseModel):
    role: Literal["student", "assistant"]
    text: str


class ChatHistory(BaseModel):
    messages: list[ChatMessage]
    last: ChatReply | None


class Slot(BaseModel):
    id: str
    mentor_id: str
    start: datetime
    end: datetime
    status: Literal["open", "booked"]


class BookingOut(BaseModel):
    id: str
    student_id: str
    mentor: PublicMentor
    slot: Slot
    status: BookingStatus
    brief: str
    created_at: datetime
    writeup_status: WriteupStatus
    # Demo only: set for the owning student's views, null for mentor and admin views.
    mentor_token: str | None = None


class Writeup(BaseModel):
    status: WriteupStatus
    discussed: list[str] = []
    work_on: list[str] = []
    next_steps: list[str] = []


class WriteupContent(BaseModel):
    discussed: list[str]
    work_on: list[str]
    next_steps: list[str]


class MentorLinkOut(BaseModel):
    booking: BookingOut
    student_name: str


class StudentIn(BaseModel):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
    email: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True,
            to_lower=True,
            max_length=254,
            pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
        ),
    ]


class StudentOut(BaseModel):
    id: str
    name: str
    email: str


class ChatIn(BaseModel):
    session_id: str | None = None
    message: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]


class BookingIn(BaseModel):
    mentor_id: str
    slot_id: str
    session_id: str | None = None


class CloseIn(BaseModel):
    outcome: Literal["completed", "no_show"]
    notes: Annotated[str, StringConstraints(max_length=8000)] | None = None


class NotesIn(BaseModel):
    notes: Annotated[str, StringConstraints(max_length=8000)]


class Funnel(BaseModel):
    chats_started: int
    matched: int
    booked: int
    completed: int
    writeups_ready: int
    rebooked: int


class UnmatchedChat(BaseModel):
    id: str
    created_at: datetime
    summary: str


class MentorLoad(BaseModel):
    mentor_id: str
    name: str
    active: int
    completed: int


class AdminSummary(BaseModel):
    funnel: Funnel
    bookings_by_status: dict[BookingStatus, int]
    stuck: list[BookingOut]
    unmatched: list[UnmatchedChat]
    mentor_load: list[MentorLoad]


class ContactIn(BaseModel):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
    email: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True,
            to_lower=True,
            max_length=254,
            pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
        ),
    ]
    message: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=4000)]


class ContactOut(BaseModel):
    id: str
    status: Literal["received"]
