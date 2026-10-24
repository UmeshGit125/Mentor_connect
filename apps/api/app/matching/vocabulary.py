"""The tags a student's need may use, read from the mentor table.

Taking the tags from the mentors themselves means every value in the sheet can be asked for, and
nothing that no mentor has is offered. A fixed list went stale: Behavioural and Consulting mentors
could never be matched.
"""

from dataclasses import dataclass

from app.matching.retrieve import domain_parts, norm, sector_parts
from app.schemas import PublicMentor

# Sheet placeholders that are not a real value to match on.
IGNORED = {"other"}


@dataclass(frozen=True)
class Vocabulary:
    domains: tuple[str, ...]
    sectors: tuple[str, ...]
    tools: tuple[str, ...]


def _unique(values: list[str]) -> tuple[str, ...]:
    """Keeps the first spelling of each value, compared without case, spaces or punctuation."""
    seen: dict[str, str] = {}
    for value in values:
        key = norm(value)
        if key and key not in IGNORED:
            seen.setdefault(key, value)
    return tuple(sorted(seen.values(), key=str.casefold))


def _tool_name(flag: str) -> str:
    return flag.replace("_", " ").title()


def tool_names(mentor: PublicMentor) -> list[str]:
    """The sheet tools this mentor is marked as using, written the way a student would name them."""
    return [_tool_name(k) for k, v in mentor.tools.model_dump().items() if v is True]


def build_vocabulary(mentors: list[PublicMentor]) -> Vocabulary:
    domains: list[str] = []
    sectors: list[str] = []
    tools: list[str] = []
    for m in mentors:
        domains += domain_parts(m.domain)
        sectors += sector_parts(m.sector) if m.sector else []
        sectors += m.sectors
        tools += tool_names(m)
        tools += m.ai_tools
    return Vocabulary(_unique(domains), _unique(sectors), _unique(tools))
