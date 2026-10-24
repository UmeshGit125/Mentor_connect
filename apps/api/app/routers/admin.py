from fastapi import APIRouter, Depends

from app.deps import Db, require_admin
from app.schemas import AdminSummary
from app.services.admin import build_summary

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/summary", response_model=AdminSummary)
def summary(db: Db) -> AdminSummary:
    return build_summary(db)
