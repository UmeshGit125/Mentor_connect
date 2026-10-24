"""Live LLM (OpenRouter) implementations of the four AI Protocols.

Every public method catches any failure, logs a warning and answers with the matching Fake*
implementation, so a student never sees an error from this layer. Model output is untrusted:
it is schema-checked here, and matches and write-ups are verified again by code.
"""

import json
import logging
import os
import re
from typing import Any

from app.ai import prompts
from app.ai.fake import (
    DEFAULT_VOCABULARY,
    SENSITIVE,
    FakeBriefWriter,
    FakeIntakeAnalyzer,
    FakeMatchExplainer,
    FakeWriteupWriter,
    _mentions,
)
from app.ai.interface import (
    BriefWriter,
    IntakeAnalyzer,
    IntakeResult,
    MatchExplainer,
    WriteupWriter,
)
from app.ai.openrouter import OpenRouter
from app.ai.verify_writeup import SECTIONS, verify_writeup
from app.matching.verify import verify_matches
from app.matching.vocabulary import Vocabulary, tool_names
from app.schemas import Match, Need, PublicMentor, Reason, WriteupContent

log = logging.getLogger("mentor_connect.ai")

DEFAULT_MODEL = "openai/gpt-4o-mini"
TIMEOUT_SECONDS = 20.0
MAX_TOKENS = 4000  # room for the JSON; truncation is treated as failure
MAX_CANDIDATES = 8
MAX_BRIEF_WORDS = 80
MAX_QUESTION_CHARS = 200
MAX_SUMMARY_CHARS = 200

# Fields of a PublicMentor row that a reason may cite (tools and activities are not citable).
CITABLE_FIELDS = (
    "domain",
    "company",
    "city",
    "sector",
    "sectors",
    "roles",
    "seniority",
    "built_ai",
    "ai_tools",
    "tools",
    "quality",
)

# Contact data must never reach a prompt.
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
_PHONE = re.compile(r"(?<!\w)\+?\d(?:[\s().-]?\d){8,}(?!\w)")
_LINKEDIN = re.compile(r"\S*linkedin\.com\S*", re.IGNORECASE)
_CONTACT_PATTERNS = (_EMAIL, _PHONE, _LINKEDIN)


class LiveAiError(Exception):
    """The model answer cannot be used. Always handled by falling back to the Fake*."""


def redact_contacts(text: str) -> str:
    """Removes emails, phone numbers and LinkedIn links from user-supplied text."""
    for pattern in _CONTACT_PATTERNS:
        text = pattern.sub("[removed]", text)
    return text


def assert_no_contact_data(*prompt_parts: str) -> None:
    """Raises if any email, phone number or LinkedIn link is in the final prompt text."""
    for part in prompt_parts:
        for pattern in _CONTACT_PATTERNS:
            found = pattern.search(part)
            if found:
                raise LiveAiError(f"Contact data found in prompt ({pattern.pattern[:12]}...).")


def _tag(name: str, text: str) -> str:
    """Wraps untrusted text in a tag. '<' is escaped so the text cannot close the tag."""
    return f"<{name}>\n{redact_contacts(text).replace('<', '&lt;')}\n</{name}>"


def _enum_list(values: list[str]) -> dict:
    return {"type": "array", "items": {"type": "string", "enum": values}}


def _strings(value: Any) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        raise LiveAiError("Expected a list of strings.")
    return value


class _LiveBase:
    """Shared plumbing: lazy client, one JSON call, strict parsing."""

    def __init__(self, client: Any = None, model: str | None = None) -> None:
        self._client = client
        self.model = model or os.environ.get("OPENROUTER_MODEL") or DEFAULT_MODEL

    @property
    def client(self) -> Any:
        if self._client is None:
            from app.config import get_settings

            self._client = OpenRouter(get_settings().llm_api_key, TIMEOUT_SECONDS)
        return self._client

    def _ask(self, system: str, user: str, schema: dict) -> dict:
        """One structured call. Returns the parsed JSON object or raises LiveAiError."""
        assert_no_contact_data(system, user)
        response = self.client.messages.create(
            model=self.model,
            max_tokens=MAX_TOKENS,
            system=system,
            messages=[{"role": "user", "content": user}],
            output_config={"format": {"type": "json_schema", "schema": schema}},
        )
        if response.stop_reason in ("refusal", "max_tokens"):
            raise LiveAiError(f"Model stopped with {response.stop_reason}.")
        text = next((b.text for b in response.content or [] if b.type == "text"), None)
        if not text or not text.strip():
            raise LiveAiError("Empty model answer.")
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise LiveAiError("Model answer is not valid JSON.") from exc
        if not isinstance(data, dict):
            raise LiveAiError("Model answer is not a JSON object.")
        return data


def _warn(step: str, exc: Exception) -> None:
    # Type and message only: never log prompts, which hold student text.
    log.warning("Live AI %s failed, using fallback: %s: %s", step, type(exc).__name__, exc)


def intake_schema(vocab: Vocabulary) -> dict:
    """The reply format. Tags may only be values that exist in the mentor table."""
    return {
        "type": "object",
        "properties": {
            "verdict": {
                "type": "string",
                "enum": ["career_problem", "vague", "off_topic", "sensitive"],
            },
            "sensitive_topic": {
                "type": "string",
                "enum": [*SENSITIVE, "none"],
            },
            "summary": {"type": "string"},
            "domains": _enum_list(list(vocab.domains)),
            "sectors": _enum_list(list(vocab.sectors)),
            "tools": _enum_list(list(vocab.tools)),
            "wants_ai": {"type": "boolean"},
            "question": {"type": "string"},
        },
        "required": [
            "verdict",
            "sensitive_topic",
            "summary",
            "domains",
            "sectors",
            "tools",
            "wants_ai",
            "question",
        ],
        "additionalProperties": False,
    }


class LiveIntakeAnalyzer(_LiveBase):
    def __init__(
        self, client: Any = None, model: str | None = None, fallback: IntakeAnalyzer | None = None
    ) -> None:
        super().__init__(client, model)
        self.fallback = fallback or FakeIntakeAnalyzer()

    def analyze(
        self, student_messages: list[str], vocabulary: Vocabulary | None = None
    ) -> IntakeResult:
        vocab = vocabulary or DEFAULT_VOCABULARY
        try:
            return self._analyze(student_messages, vocab)
        except Exception as exc:
            _warn("intake", exc)
            return self.fallback.analyze(student_messages, vocab)

    def _analyze(self, student_messages: list[str], vocab: Vocabulary) -> IntakeResult:
        if not student_messages:
            raise LiveAiError("No student messages.")
        user = "\n".join(_tag("student_message", m) for m in student_messages)
        data = self._ask(prompts.INTAKE_SYSTEM, user, intake_schema(vocab))
        verdict = data.get("verdict")

        # Safety net: a clear self harm phrase is never routed to mentor matching.
        if _mentions(student_messages[-1].casefold(), SENSITIVE["self_harm"]):
            return IntakeResult("sensitive", topic="self_harm")
        if verdict == "sensitive":
            topic = data.get("sensitive_topic")
            return IntakeResult("sensitive", topic=topic if topic in SENSITIVE else "mental_health")
        if verdict == "off_topic":
            return IntakeResult("off_topic")
        if verdict == "vague":
            question = data.get("question")
            question = " ".join(question.split()) if isinstance(question, str) else ""
            return IntakeResult("vague", question=question[:MAX_QUESTION_CHARS] or None)
        if verdict != "career_problem":
            raise LiveAiError("Unknown verdict.")

        summary = data.get("summary")
        wants_ai = data.get("wants_ai")
        if not isinstance(summary, str) or not summary.strip() or not isinstance(wants_ai, bool):
            raise LiveAiError("Bad need fields.")
        need = Need(
            summary=" ".join(redact_contacts(summary).split())[:MAX_SUMMARY_CHARS],
            domains=_strings(data.get("domains")),
            sectors=_strings(data.get("sectors")),
            tools=_strings(data.get("tools")),
            wants_ai=wants_ai,
        )
        return IntakeResult("ok", need)


EXPLAIN_SCHEMA = {
    "type": "object",
    "properties": {
        "matches": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "mentor_id": {"type": "string"},
                    "reasons": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "field": {"type": "string"},
                                "value": {"type": "string"},
                                "text": {"type": "string"},
                            },
                            "required": ["field", "value", "text"],
                            "additionalProperties": False,
                        },
                    },
                },
                "required": ["mentor_id", "reasons"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["matches"],
    "additionalProperties": False,
}


def candidate_row(mentor: PublicMentor) -> dict[str, Any]:
    """The only view of a mentor the model sees: citable, non-blank fields. No name or contact."""
    row: dict[str, Any] = {"mentor_id": mentor.id}
    for name in CITABLE_FIELDS:
        value = tool_names(mentor) if name == "tools" else getattr(mentor, name)
        if value is None or value == []:
            continue
        row[name] = str(value) if isinstance(value, bool) else value
    return row


class LiveMatchExplainer(_LiveBase):
    def __init__(
        self, client: Any = None, model: str | None = None, fallback: MatchExplainer | None = None
    ) -> None:
        super().__init__(client, model)
        self.fallback = fallback or FakeMatchExplainer()

    def explain(self, need: Need, candidates: list[PublicMentor]) -> list[Match]:
        try:
            return self._explain(need, candidates[:MAX_CANDIDATES])
        except Exception as exc:
            _warn("explain", exc)
            return self.fallback.explain(need, candidates)

    def _explain(self, need: Need, candidates: list[PublicMentor]) -> list[Match]:
        if not candidates:
            return []
        payload = {
            "need": need.model_dump(),
            "candidates": [candidate_row(m) for m in candidates],
        }
        # The need summary comes from the student, so it is wrapped like any student text.
        user = (
            _tag("student_message", need.summary)
            + "\n<data>\n"
            + json.dumps({**payload, "need": {**payload["need"], "summary": ""}}, indent=1)
            + "\n</data>"
        )
        data = self._ask(prompts.EXPLAIN_SYSTEM, user, EXPLAIN_SCHEMA)
        raw_matches = data.get("matches")
        if not isinstance(raw_matches, list):
            raise LiveAiError("Missing matches list.")
        rows = {m.id: m for m in candidates}
        raw: list[Match] = []
        for item in raw_matches:
            if not isinstance(item, dict) or item.get("mentor_id") not in rows:
                continue
            reasons = [
                Reason(field=r["field"], value=r["value"], text=redact_contacts(str(r["text"])))
                for r in item.get("reasons", [])
            ]
            raw.append(Match(mentor=rows[item["mentor_id"]], reasons=reasons))
        verified = verify_matches(raw, candidates)
        if raw_matches and not verified:
            raise LiveAiError("No model match passed verification.")
        return verified


BRIEF_SCHEMA = {
    "type": "object",
    "properties": {"brief": {"type": "string"}},
    "required": ["brief"],
    "additionalProperties": False,
}


class LiveBriefWriter(_LiveBase):
    def __init__(
        self, client: Any = None, model: str | None = None, fallback: BriefWriter | None = None
    ) -> None:
        super().__init__(client, model)
        self.fallback = fallback or FakeBriefWriter()

    def write(self, need: Need | None, student_messages: list[str]) -> str:
        try:
            return self._write(student_messages)
        except Exception as exc:
            _warn("brief", exc)
            return self.fallback.write(need, student_messages)

    def _write(self, student_messages: list[str]) -> str:
        if not any(m.strip() for m in student_messages):
            raise LiveAiError("No student messages.")
        user = "\n".join(_tag("student_message", m) for m in student_messages)
        data = self._ask(prompts.BRIEF_SYSTEM, user, BRIEF_SCHEMA)
        brief = data.get("brief")
        if not isinstance(brief, str) or not brief.strip():
            raise LiveAiError("Empty brief.")
        words = redact_contacts(brief).split()
        return " ".join(words[:MAX_BRIEF_WORDS])


_ITEM = {
    "type": "object",
    "properties": {"text": {"type": "string"}, "quote": {"type": "string"}},
    "required": ["text", "quote"],
    "additionalProperties": False,
}
WRITEUP_SCHEMA = {
    "type": "object",
    "properties": {name: {"type": "array", "items": _ITEM} for name in SECTIONS},
    "required": list(SECTIONS),
    "additionalProperties": False,
}


class LiveWriteupWriter(_LiveBase):
    def __init__(
        self, client: Any = None, model: str | None = None, fallback: WriteupWriter | None = None
    ) -> None:
        super().__init__(client, model)
        self.fallback = fallback or FakeWriteupWriter()

    def write(self, notes: str) -> WriteupContent | None:
        if not notes.strip():
            return None  # empty notes never reach the model
        try:
            return self._write(notes)
        except Exception as exc:
            _warn("writeup", exc)
            return self.fallback.write(notes)

    def _write(self, notes: str) -> WriteupContent | None:
        # Quotes are checked against the notes exactly as the model saw them.
        seen = redact_contacts(notes)
        data = self._ask(prompts.WRITEUP_SYSTEM, _tag("call_notes", notes), WRITEUP_SCHEMA)
        for name in SECTIONS:
            if not isinstance(data.get(name), list):
                raise LiveAiError(f"Missing section {name}.")
        content = verify_writeup(data, seen.replace("<", "&lt;"))
        # Model output is scrubbed too, so contact data cannot reach a student through a write-up.
        content = WriteupContent(
            **{
                name: [redact_contacts(item) for item in getattr(content, name)]
                for name in SECTIONS
            }
        )
        if any((content.discussed, content.work_on, content.next_steps)):
            return content
        if any(data[name] for name in SECTIONS):
            raise LiveAiError("No model item was backed by the notes.")
        return None
