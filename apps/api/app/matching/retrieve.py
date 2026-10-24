import re
from dataclasses import dataclass

from app.schemas import Need, PublicMentor

DOMAIN_WEIGHT = 3.0
SECTOR_WEIGHT = 2.0
LIST_MATCH_WEIGHT = 1.5
# The six tool flags in the sheet are common (a fifth of mentors have Tableau), so two of them must
# never outweigh the one domain the student actually asked for. AI tools are rarer and stay at 1.5.
TOOL_WEIGHT = 1.0
AI_WEIGHT = 1.0
QUALITY_BONUS = {"Excellent": 0.2, "Good": 0.1}
# Matches how many candidates the explainer is told it may look at.
DEFAULT_LIMIT = 8
_SECTOR_SPLIT = re.compile(r"\s/\s")


@dataclass(frozen=True)
class Overlap:
    """One place where a mentor row meets the student's need."""

    field: str
    value: str
    weight: float


@dataclass(frozen=True)
class Candidate:
    mentor: PublicMentor
    score: float


def norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.casefold())


def domain_parts(domain: str) -> list[str]:
    """A mentor can list two domains in one cell: "Business Generalist, Growth"."""
    return [p.strip() for p in domain.split(",") if p.strip()]


def sector_parts(sector: str) -> list[str]:
    """The sheet writes two sectors as "Healthtech / Medtech". Each side is its own sector."""
    return [p.strip() for p in _SECTOR_SPLIT.split(sector) if p.strip()]


def find_overlaps(mentor: PublicMentor, need: Need) -> list[Overlap]:
    """Overlaps between the need and non-null fields of the mentor. Quality is not one."""
    found: list[Overlap] = []

    for domain in need.domains:
        wanted = domain.casefold()
        # Whole names only. A substring test let "AI" or "Data" hit words that merely contain them.
        word = re.compile(rf"(?<![a-z0-9]){re.escape(wanted)}(?![a-z0-9])")
        role = next((r for r in mentor.roles if word.search(r.casefold())), None)
        if any(wanted == part.casefold() for part in domain_parts(mentor.domain)):
            found.append(Overlap("domain", mentor.domain, DOMAIN_WEIGHT))
        elif role:
            found.append(Overlap("roles", role, LIST_MATCH_WEIGHT))

    for sector in need.sectors:
        wanted = norm(sector)
        listed = next((s for s in mentor.sectors if norm(s) == wanted), None)
        # Exact sector names only: "Edtech" is a substring of "Medtech" but is a different sector.
        main = mentor.sector and (
            wanted == norm(mentor.sector)
            or any(wanted == norm(part) for part in sector_parts(mentor.sector))
        )
        if main:
            found.append(Overlap("sector", mentor.sector, SECTOR_WEIGHT))
        elif listed:
            found.append(Overlap("sectors", listed, LIST_MATCH_WEIGHT))

    for tool in need.tools:
        has_tool = {norm(k) for k, v in mentor.tools.model_dump().items() if v is True}
        ai_tool = next((t for t in mentor.ai_tools if norm(t) == norm(tool)), None)
        if norm(tool) in has_tool:
            found.append(Overlap("tools", tool, TOOL_WEIGHT))
        elif ai_tool:
            found.append(Overlap("ai_tools", ai_tool, LIST_MATCH_WEIGHT))

    ai_cited = any(o.field == "ai_tools" for o in found)
    if need.wants_ai and not ai_cited:
        if mentor.ai_tools:
            found.append(Overlap("ai_tools", mentor.ai_tools[0], AI_WEIGHT))
        elif mentor.built_ai is True:
            found.append(Overlap("built_ai", "True", AI_WEIGHT))

    return found


def score(mentor: PublicMentor, need: Need) -> float:
    overlaps = find_overlaps(mentor, need)
    if not overlaps:
        return 0.0
    # Quality only breaks ties. A null quality adds nothing and costs nothing.
    return sum(o.weight for o in overlaps) + QUALITY_BONUS.get(mentor.quality or "", 0.0)


def top_candidates(
    mentors: list[PublicMentor], need: Need, limit: int = DEFAULT_LIMIT
) -> list[Candidate]:
    scored = [Candidate(m, score(m, need)) for m in mentors]
    ranked = sorted((c for c in scored if c.score > 0), key=lambda c: (-c.score, c.mentor.id))
    return ranked[:limit]
