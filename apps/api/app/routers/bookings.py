from fastapi import APIRouter
from sqlalchemy import select

from app.deps import Ai, CurrentStudent, Db, ViewerId
from app.models import Booking
from app.schemas import BookingIn, BookingOut, Writeup
from app.services import bookings

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("", response_model=BookingOut, status_code=201)
def create(body: BookingIn, db: Db, ai: Ai, student: CurrentStudent) -> BookingOut:
    booking = bookings.create_booking(
        db, ai, student, body.mentor_id, body.slot_id, body.session_id
    )
    return bookings.booking_out(booking, include_token=True)


@router.get("", response_model=list[BookingOut])
def list_mine(db: Db, student: CurrentStudent) -> list[BookingOut]:
    rows = db.scalars(
        select(Booking).where(Booking.student_id == student.id).order_by(Booking.created_at)
    )
    return [bookings.booking_out(b, include_token=True) for b in rows]


@router.get("/{booking_id}", response_model=BookingOut)
def get_one(booking_id: str, db: Db, viewer: ViewerId = None) -> BookingOut:
    return bookings.booking_out(bookings.get_owned(db, booking_id, viewer), include_token=True)


@router.post("/{booking_id}/cancel", response_model=BookingOut)
def cancel(booking_id: str, db: Db, viewer: ViewerId = None) -> BookingOut:
    booking = bookings.cancel_booking(db, bookings.get_owned(db, booking_id, viewer))
    return bookings.booking_out(booking, include_token=True)


@router.get("/{booking_id}/writeup", response_model=Writeup)
def get_writeup(booking_id: str, db: Db, viewer: ViewerId = None) -> Writeup:
    return bookings.writeup_out(bookings.get_owned(db, booking_id, viewer))
