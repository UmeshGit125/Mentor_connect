import secrets
from datetime import timedelta

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.deps import AiServices
from app.errors import ApiError, invalid_state, not_found, validation_error
from app.models import Booking, ChatSession, Mentor, Slot, Student, Writeup, utcnow
from app.schemas import BookingOut, Need, PublicMentor
from app.schemas import Slot as SlotOut
from app.schemas import Writeup as WriteupOut

MAX_ACTIVE_PER_STUDENT = 3
MAX_PER_MENTOR_PER_WEEK = 5
WEEK = timedelta(days=7)
NO_CHAT_BRIEF = "Booked without a chat"


def slot_out(slot: Slot) -> SlotOut:
    return SlotOut(
        id=slot.id, mentor_id=slot.mentor_id, start=slot.start, end=slot.end, status=slot.status
    )


def booking_out(booking: Booking, include_token: bool = False) -> BookingOut:
    return BookingOut(
        id=booking.id,
        student_id=booking.student_id,
        mentor=PublicMentor.model_validate(booking.mentor),
        slot=slot_out(booking.slot),
        status=booking.status,
        brief=booking.brief,
        created_at=booking.created_at,
        writeup_status=booking.writeup.status if booking.writeup else "none",
        mentor_token=booking.mentor_token if include_token else None,
    )


def open_slots(db: Session, mentor_id: str) -> list[Slot]:
    if db.get(Mentor, mentor_id) is None:
        raise not_found("We could not find that mentor.")
    now = utcnow()
    query = (
        select(Slot)
        .where(
            Slot.mentor_id == mentor_id,
            Slot.status == "open",
            Slot.start > now,
            Slot.start < now + WEEK,
        )
        .order_by(Slot.start)
    )
    return list(db.scalars(query))


def _check_caps(db: Session, student_id: str, mentor_id: str) -> None:
    active = db.scalar(
        select(func.count())
        .select_from(Booking)
        .where(Booking.student_id == student_id, Booking.status == "confirmed")
    )
    if active >= MAX_ACTIVE_PER_STUDENT:
        raise ApiError(
            409,
            "booking_cap_reached",
            "You already have 3 upcoming calls. Finish or cancel one to book another.",
        )
    # Counts calls from the last week or still to come. Cancelled and no-show calls free up room.
    for_mentor = db.scalar(
        select(func.count())
        .select_from(Booking)
        .join(Slot, Booking.slot_id == Slot.id)
        .where(
            Booking.mentor_id == mentor_id,
            Booking.status.in_(["confirmed", "completed"]),
            Slot.start > utcnow() - WEEK,
        )
    )
    if for_mentor >= MAX_PER_MENTOR_PER_WEEK:
        raise ApiError(
            409,
            "mentor_cap_reached",
            "This mentor is fully booked this week. Please pick another mentor.",
        )


def create_booking(
    db: Session,
    ai: AiServices,
    student: Student,
    mentor_id: str,
    slot_id: str,
    session_id: str | None,
) -> Booking:
    session = db.get(ChatSession, session_id) if session_id else None
    if session_id and (session is None or session.student_id != student.id):
        raise not_found("We could not find that chat.")
    slot = db.get(Slot, slot_id)
    if slot is None or db.get(Mentor, mentor_id) is None:
        raise not_found("We could not find that slot.")
    if slot.mentor_id != mentor_id:
        raise validation_error("That slot does not belong to this mentor.")

    # Single conditional UPDATE: only one concurrent caller can flip open to booked.
    claimed = db.execute(
        update(Slot)
        .where(Slot.id == slot_id, Slot.status == "open", Slot.start > utcnow())
        .values(status="booked")
    ).rowcount
    if claimed != 1:
        db.rollback()
        raise ApiError(409, "slot_taken", "That slot was just booked. Pick another time.")
    try:
        _check_caps(db, student.id, mentor_id)
    except ApiError:
        db.rollback()
        raise

    need = Need.model_validate(session.need) if session and session.need else None
    texts = [m.text for m in session.messages if m.role == "student"] if session else []
    booking = Booking(
        student_id=student.id,
        mentor_id=mentor_id,
        slot_id=slot_id,
        session_id=session_id or None,
        brief=ai.brief.write(need, texts) if session else NO_CHAT_BRIEF,
        mentor_token=secrets.token_urlsafe(32),
    )
    db.add(booking)
    db.commit()
    db.refresh(slot)
    return booking


def get_owned(db: Session, booking_id: str, viewer_id: str | None) -> Booking:
    """A student only sees their own bookings. No header means no ownership check (demo)."""
    booking = db.get(Booking, booking_id)
    if booking is None or (viewer_id is not None and booking.student_id != viewer_id):
        raise not_found("We could not find that booking.")
    return booking


def cancel_booking(db: Session, booking: Booking) -> Booking:
    if booking.status != "confirmed":
        raise invalid_state("Only an upcoming call can be cancelled.")
    booking.status = "cancelled"
    booking.slot.status = "open"
    db.commit()
    return booking


def by_token(db: Session, token: str) -> Booking:
    booking = db.scalar(select(Booking).where(Booking.mentor_token == token))
    if booking is None:
        raise not_found("We could not find that link.")
    return booking


def _generate_writeup(db: Session, ai: AiServices, booking: Booking, notes: str) -> None:
    if not notes.strip():
        return
    try:
        content = ai.writeup.write(notes)
    except Exception:
        content = None
        failed = True  # notes are kept, status stays notes_received
    else:
        failed = False
    if content is None and not failed:
        return  # nothing to report: no write-up row, status stays "none"
    writeup = Writeup(booking_id=booking.id, notes=notes, status="notes_received")
    db.add(writeup)
    if content is not None:
        writeup.discussed, writeup.work_on = content.discussed, content.work_on
        writeup.next_steps = content.next_steps
        writeup.status = "ready"
    booking.writeup = writeup


def close_booking(
    db: Session, ai: AiServices, booking: Booking, outcome: str, notes: str | None
) -> Booking:
    if booking.status != "confirmed":
        raise invalid_state("This call has already been closed.")
    booking.status = outcome
    if outcome == "completed" and notes:
        _generate_writeup(db, ai, booking, notes)
    db.commit()
    return booking


def add_notes(db: Session, ai: AiServices, booking: Booking, notes: str) -> Booking:
    if booking.status != "completed":
        raise invalid_state("Notes can only be added to a completed call.")
    if not notes.strip():
        raise validation_error("Notes cannot be empty.")
    if booking.writeup is not None:
        raise invalid_state("Notes were already added for this call.")
    _generate_writeup(db, ai, booking, notes)
    db.commit()
    return booking


def writeup_out(booking: Booking) -> WriteupOut:
    w = booking.writeup
    if w is None:
        return WriteupOut(status="none")
    if w.status != "ready":
        return WriteupOut(status=w.status)
    return WriteupOut(
        status="ready", discussed=w.discussed, work_on=w.work_on, next_steps=w.next_steps
    )
