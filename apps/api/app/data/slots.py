"""SAMPLE DATA: availability for every mentor is generated here, it is not from the sheet.

The pattern is deterministic per mentor and day, so running it twice adds nothing new.
"""

import random
from datetime import datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Mentor, Slot, utcnow

SLOT_MINUTES = 30
DAYS_AHEAD = 7
LEAD_TIME = timedelta(hours=1)
# 10:00 to 18:00 India time, written in UTC.
FIRST_START = time(4, 30)
STARTS_PER_DAY = 16
SLOTS_PER_DAY = (2, 4)


def _day_slots(mentor_id: str, day: datetime) -> list[datetime]:
    rng = random.Random(f"{mentor_id}:{day.date().isoformat()}")
    first = datetime.combine(day.date(), FIRST_START)
    grid = [first + timedelta(minutes=SLOT_MINUTES * i) for i in range(STARTS_PER_DAY)]
    return sorted(rng.sample(grid, rng.randint(*SLOTS_PER_DAY)))


def seed_slots(db: Session, now: datetime | None = None) -> int:
    """Adds missing open slots for the next week. Returns how many were added."""
    now = now or utcnow()
    earliest = now + LEAD_TIME
    existing = {(s.mentor_id, s.start) for s in db.execute(select(Slot)).scalars() if s.start > now}
    added = 0
    for mentor_id in db.execute(select(Mentor.id).order_by(Mentor.id)).scalars():
        for offset in range(DAYS_AHEAD + 1):
            for start in _day_slots(mentor_id, now + timedelta(days=offset)):
                if start <= earliest or (mentor_id, start) in existing:
                    continue
                end = start + timedelta(minutes=SLOT_MINUTES)
                db.add(Slot(mentor_id=mentor_id, start=start, end=end, status="open"))
                added += 1
    db.commit()
    return added
