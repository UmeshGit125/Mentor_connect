import time
from collections import defaultdict, deque

from fastapi import APIRouter, Request

from app.deps import Db
from app.errors import ApiError
from app.models import ContactMessage
from app.schemas import ContactIn, ContactOut

router = APIRouter(tags=["contact"])

# Simple per-IP limit: at most 5 messages per 10 minutes, kept in memory per process.
LIMIT = 5
WINDOW_SECONDS = 600
_recent: dict[str, deque[float]] = defaultdict(deque)


def _check_rate(ip: str) -> None:
    now = time.monotonic()
    hits = _recent[ip]
    while hits and now - hits[0] > WINDOW_SECONDS:
        hits.popleft()
    if len(hits) >= LIMIT:
        raise ApiError(429, "rate_limited", "Too many messages. Please try again in a few minutes.")
    hits.append(now)


@router.post("/contact", response_model=ContactOut, status_code=201)
def create_contact(body: ContactIn, request: Request, db: Db) -> ContactMessage:
    _check_rate(request.client.host if request.client else "unknown")
    row = ContactMessage(name=body.name, email=body.email, message=body.message)
    db.add(row)
    db.commit()
    return ContactOut(id=row.id, status="received")
