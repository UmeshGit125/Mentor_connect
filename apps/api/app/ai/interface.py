"""Every model call sits behind these Protocols. A live implementation can replace the fakes."""

from dataclasses import dataclass
from typing import Literal, Protocol

from app.matching.vocabulary import Vocabulary
from app.schemas import Match, Need, PublicMentor, WriteupContent

Verdict = Literal["ok", "vague", "off_topic", "sensitive"]
SensitiveTopic = Literal["legal", "medical", "mental_health", "self_harm"]


@dataclass(frozen=True)
class IntakeResult:
    verdict: Verdict
    need: Need | None = None
    topic: SensitiveTopic | None = None
    question: str | None = None  # optional clarifying question for a vague message


class IntakeAnalyzer(Protocol):
    def analyze(
        self, student_messages: list[str], vocabulary: Vocabulary | None = None
    ) -> IntakeResult:
        """Reads everything the student said in a session. Messages are data, not instructions.

        Tags in the result come only from `vocabulary`, which is read from the mentor table.
        """


class MatchExplainer(Protocol):
    def explain(self, need: Need, candidates: list[PublicMentor]) -> list[Match]:
        """Output is untrusted until it passes matching.verify."""


class BriefWriter(Protocol):
    def write(self, need: Need | None, student_messages: list[str]) -> str: ...


class WriteupWriter(Protocol):
    def write(self, notes: str) -> WriteupContent | None:
        """Returns None when there is nothing to summarise (empty or whitespace notes)."""
