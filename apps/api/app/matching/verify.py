from app.matching.retrieve import norm
from app.schemas import Match, PublicMentor, Reason

MAX_MATCHES = 3
MAX_REASONS = 3
# Fields a student's need can overlap. Quality, city and the like are facts about the mentor, not a
# reason the mentor fits, so a match backed only by those is dropped.
FIT_FIELDS = {"domain", "roles", "sector", "sectors", "tools", "ai_tools", "built_ai"}


def _has_tool(mentor: PublicMentor, value: str) -> bool:
    return any(norm(k) == norm(value) and v is True for k, v in mentor.tools.model_dump().items())


def _cites_row(mentor: PublicMentor, reason: Reason) -> bool:
    """True only if the field is non-null on the row and the value is exactly what is stored."""
    if reason.field not in PublicMentor.model_fields:
        return False
    if reason.field == "tools":
        return bool(reason.text.strip()) and _has_tool(mentor, reason.value)
    stored = getattr(mentor, reason.field)
    if stored is None or stored == [] or not reason.text.strip():
        return False
    if isinstance(stored, list):
        return reason.value in stored
    return reason.value == str(stored)


def verify_matches(
    raw: list[Match], candidates: list[PublicMentor], limit: int = MAX_MATCHES
) -> list[Match]:
    """Keeps only explainer output that is backed by the candidate rows.

    A match is dropped if its mentor is not a candidate, or if any reason cites a null field or a
    value that differs from the row. The mentor shown is always the stored row, never the model's.
    """
    rows = {m.id: m for m in candidates}
    verified: list[Match] = []
    seen: set[str] = set()
    for match in raw:
        row = rows.get(match.mentor.id)
        reasons = match.reasons
        if row is None or match.mentor.id in seen or not 1 <= len(reasons) <= MAX_REASONS:
            continue
        if not all(_cites_row(row, r) for r in reasons):
            continue
        if not any(r.field in FIT_FIELDS for r in reasons):
            continue
        seen.add(row.id)
        verified.append(Match(mentor=row, reasons=reasons))
    return verified[:limit]
