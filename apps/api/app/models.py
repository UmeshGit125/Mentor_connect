import secrets
from datetime import UTC, datetime

from sqlalchemy import JSON, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    """Naive UTC, because SQLite drops tzinfo. Serialised as UTC in the API layer."""
    return datetime.now(UTC).replace(tzinfo=None)


def new_id() -> str:
    return secrets.token_urlsafe(16)


class Base(DeclarativeBase):
    pass


class Mentor(Base):
    __tablename__ = "mentors"

    id: Mapped[str] = mapped_column(String(16), primary_key=True)
    name: Mapped[str]
    city: Mapped[str | None]
    domain: Mapped[str]
    company: Mapped[str | None]
    sector: Mapped[str | None]
    sectors: Mapped[list[str]] = mapped_column(JSON)
    roles: Mapped[list[str]] = mapped_column(JSON)
    seniority: Mapped[str | None]
    built_ai: Mapped[bool | None]
    ai_tools: Mapped[list[str]] = mapped_column(JSON)
    tools: Mapped[dict[str, bool | None]] = mapped_column(JSON)
    quality: Mapped[str | None]
    activities: Mapped[int | None]


class Student(Base):
    __tablename__ = "students"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    name: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"), index=True)
    clarify_count: Mapped[int] = mapped_column(default=0)
    last_kind: Mapped[str | None]
    ever_matched: Mapped[bool] = mapped_column(default=False)
    need: Mapped[dict | None] = mapped_column(JSON)
    last_reply: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    messages: Mapped[list["Message"]] = relationship(order_by="Message.id")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("chat_sessions.id"), index=True)
    role: Mapped[str] = mapped_column(String(16))
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)


class Slot(Base):
    __tablename__ = "slots"
    __table_args__ = (UniqueConstraint("mentor_id", "start"),)

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    mentor_id: Mapped[str] = mapped_column(ForeignKey("mentors.id"), index=True)
    start: Mapped[datetime] = mapped_column(index=True)
    end: Mapped[datetime]
    status: Mapped[str] = mapped_column(String(16), default="open")


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"), index=True)
    mentor_id: Mapped[str] = mapped_column(ForeignKey("mentors.id"), index=True)
    slot_id: Mapped[str] = mapped_column(ForeignKey("slots.id"))
    session_id: Mapped[str | None] = mapped_column(ForeignKey("chat_sessions.id"))
    status: Mapped[str] = mapped_column(String(16), default="confirmed")
    brief: Mapped[str] = mapped_column(Text)
    mentor_token: Mapped[str] = mapped_column(unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    student: Mapped[Student] = relationship()
    mentor: Mapped[Mentor] = relationship()
    slot: Mapped[Slot] = relationship()
    writeup: Mapped["Writeup | None"] = relationship(back_populates="booking")


class Writeup(Base):
    __tablename__ = "writeups"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    booking_id: Mapped[str] = mapped_column(ForeignKey("bookings.id"), unique=True)
    notes: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16), default="notes_received")
    discussed: Mapped[list[str]] = mapped_column(JSON, default=list)
    work_on: Mapped[list[str]] = mapped_column(JSON, default=list)
    next_steps: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    booking: Mapped[Booking] = relationship(back_populates="writeup")


class ContactMessage(Base):
    """An enquiry from the public contact form. Read by the Mesa team, never shown back."""

    __tablename__ = "contact_messages"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    name: Mapped[str]
    email: Mapped[str]
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
