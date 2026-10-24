from typing import Annotated

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.deps import Db
from app.errors import not_found
from app.models import Mentor
from app.schemas import PublicMentor, Slot
from app.services import bookings

router = APIRouter(prefix="/mentors", tags=["mentors"])


def _matches_text(m: PublicMentor, q: str) -> bool:
    haystack = " ".join(
        [m.name, m.domain, m.company or "", m.sector or "", *m.sectors, *m.roles, *m.ai_tools]
    )
    return q.casefold() in haystack.casefold()


@router.get("", response_model=list[PublicMentor])
def list_mentors(
    db: Db,
    q: Annotated[str | None, Query(max_length=200)] = None,
    domain: str | None = None,
    sector: str | None = None,
    city: str | None = None,
) -> list[PublicMentor]:
    mentors = [
        PublicMentor.model_validate(m) for m in db.scalars(select(Mentor).order_by(Mentor.id))
    ]
    if q and q.strip():
        mentors = [m for m in mentors if _matches_text(m, q.strip())]
    if domain:
        mentors = [m for m in mentors if domain.casefold() in m.domain.casefold()]
    if sector:
        mentors = [m for m in mentors if (m.sector or "").casefold() == sector.strip().casefold()]
    if city:
        mentors = [m for m in mentors if (m.city or "").casefold() == city.strip().casefold()]
    return mentors


@router.get("/{mentor_id}", response_model=PublicMentor)
def get_mentor(mentor_id: str, db: Db) -> PublicMentor:
    mentor = db.get(Mentor, mentor_id)
    if mentor is None:
        raise not_found("We could not find that mentor.")
    return PublicMentor.model_validate(mentor)


@router.get("/{mentor_id}/slots", response_model=list[Slot])
def mentor_slots(mentor_id: str, db: Db) -> list[Slot]:
    return [bookings.slot_out(s) for s in bookings.open_slots(db, mentor_id)]
