from fastapi import APIRouter

from app.deps import Ai, Db
from app.schemas import BookingOut, CloseIn, MentorLinkOut, NotesIn
from app.services import bookings

router = APIRouter(prefix="/m", tags=["mentor link"])


@router.get("/{token}", response_model=MentorLinkOut)
def view(token: str, db: Db) -> MentorLinkOut:
    booking = bookings.by_token(db, token)
    return MentorLinkOut(booking=bookings.booking_out(booking), student_name=booking.student.name)


@router.post("/{token}/close", response_model=BookingOut)
def close(token: str, body: CloseIn, db: Db, ai: Ai) -> BookingOut:
    booking = bookings.close_booking(db, ai, bookings.by_token(db, token), body.outcome, body.notes)
    return bookings.booking_out(booking)


@router.post("/{token}/notes", response_model=BookingOut)
def notes(token: str, body: NotesIn, db: Db, ai: Ai) -> BookingOut:
    booking = bookings.add_notes(db, ai, bookings.by_token(db, token), body.notes)
    return bookings.booking_out(booking)
