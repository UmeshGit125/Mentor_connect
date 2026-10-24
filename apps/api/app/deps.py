import hmac
from dataclasses import dataclass
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.ai.fake import FakeBriefWriter, FakeIntakeAnalyzer, FakeMatchExplainer, FakeWriteupWriter
from app.ai.interface import BriefWriter, IntakeAnalyzer, MatchExplainer, WriteupWriter
from app.ai.live import (
    LiveBriefWriter,
    LiveIntakeAnalyzer,
    LiveMatchExplainer,
    LiveWriteupWriter,
)
from app.config import get_settings
from app.db import get_db
from app.errors import ApiError, not_found, validation_error
from app.models import Student

Db = Annotated[Session, Depends(get_db)]


@dataclass(frozen=True)
class AiServices:
    mode: str
    intake: IntakeAnalyzer
    explainer: MatchExplainer
    brief: BriefWriter
    writeup: WriteupWriter


@lru_cache
def get_ai() -> AiServices:
    settings = get_settings()
    if settings.llm_api_key and settings.use_live_ai:
        # Each Live class falls back to its Fake on any failure, so "live" never errors.
        return AiServices(
            "live",
            LiveIntakeAnalyzer(),
            LiveMatchExplainer(),
            LiveBriefWriter(),
            LiveWriteupWriter(),
        )
    return AiServices(
        "fallback",
        FakeIntakeAnalyzer(),
        FakeMatchExplainer(),
        FakeBriefWriter(),
        FakeWriteupWriter(),
    )


Ai = Annotated[AiServices, Depends(get_ai)]


def optional_student_id(x_student_id: Annotated[str | None, Header()] = None) -> str | None:
    return x_student_id


def current_student(db: Db, x_student_id: Annotated[str | None, Header()] = None) -> Student:
    if not x_student_id:
        raise validation_error("X-Student-Id header is required.")
    student = db.get(Student, x_student_id)
    if student is None:
        raise not_found("We could not find that student.")
    return student


CurrentStudent = Annotated[Student, Depends(current_student)]
ViewerId = Annotated[str | None, Depends(optional_student_id)]


def require_admin(x_admin_password: Annotated[str | None, Header()] = None) -> None:
    expected = get_settings().admin_password.encode()
    given = (x_admin_password or "").encode()
    if not hmac.compare_digest(given, expected):
        raise ApiError(401, "unauthorized", "Admin password is missing or wrong.")
