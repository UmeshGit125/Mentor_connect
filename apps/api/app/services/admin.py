from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Booking, ChatSession, Mentor, Slot, utcnow
from app.schemas import AdminSummary, Funnel, MentorLoad, UnmatchedChat
from app.services.bookings import booking_out

STUCK_AFTER = timedelta(days=2)
STATUSES = ("confirmed", "completed", "no_show", "cancelled")


def _rebooked(bookings: list[Booking]) -> int:
    """Bookings where the student had already completed a call with the same mentor."""
    count = 0
    for b in bookings:
        count += any(
            o.student_id == b.student_id
            and o.mentor_id == b.mentor_id
            and o.status == "completed"
            and o.created_at < b.created_at
            for o in bookings
        )
    return count


def build_summary(db: Session) -> AdminSummary:
    bookings = list(db.scalars(select(Booking).order_by(Booking.created_at)))
    sessions = list(db.scalars(select(ChatSession).order_by(ChatSession.created_at)))
    by_status = {s: sum(b.status == s for b in bookings) for s in STATUSES}
    writeups_ready = sum(1 for b in bookings if b.writeup and b.writeup.status == "ready")

    cutoff = utcnow() - STUCK_AFTER
    stuck = db.scalars(
        select(Booking)
        .join(Slot, Booking.slot_id == Slot.id)
        .where(Booking.status == "confirmed", Slot.end < cutoff)
        .order_by(Slot.end)
    )
    unmatched = [
        UnmatchedChat(id=s.id, created_at=s.created_at, summary=(s.need or {}).get("summary", ""))
        for s in sessions
        if s.last_kind == "no_match"
    ]
    load = [
        MentorLoad(
            mentor_id=m.id,
            name=m.name,
            active=sum(b.mentor_id == m.id and b.status == "confirmed" for b in bookings),
            completed=sum(b.mentor_id == m.id and b.status == "completed" for b in bookings),
        )
        for m in db.scalars(select(Mentor).order_by(Mentor.id))
    ]
    return AdminSummary(
        funnel=Funnel(
            chats_started=len(sessions),
            matched=sum(s.ever_matched for s in sessions),
            booked=len(bookings),
            completed=by_status["completed"],
            writeups_ready=writeups_ready,
            rebooked=_rebooked(bookings),
        ),
        bookings_by_status=by_status,
        stuck=[booking_out(b) for b in stuck],
        unmatched=unmatched,
        mentor_load=load,
    )
