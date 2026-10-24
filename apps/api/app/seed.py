"""Loads the cleaned mentor sheet and sample slots. Run with: python -m app.seed"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.data.clean import CleaningReport, clean_mentors
from app.data.slots import seed_slots
from app.db import SessionLocal, engine
from app.models import Base, Mentor


def seed_mentors(db: Session) -> CleaningReport:
    mentors, report = clean_mentors(get_settings().mentors_xlsx)
    for mentor in mentors:
        db.merge(Mentor(**mentor.model_dump()))
    db.commit()
    return report


def seed_all(db: Session, always_report: bool = False) -> CleaningReport | None:
    """Seeds mentors when the table is empty, and always tops up slots."""
    report = None
    if always_report or not db.scalar(select(func.count()).select_from(Mentor)):
        report = seed_mentors(db)
    seed_slots(db)
    return report


def main() -> None:
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        report = seed_all(db, always_report=True)
    if report:
        print(report.format())


if __name__ == "__main__":
    main()
