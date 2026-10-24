# ruff: noqa: E501
"""A scripted stand-in for `anthropic.Anthropic`. It only has `.messages.create(**kwargs)`.

Every call is recorded (`fake.calls`) so tests can read the full prompt text. Responses are
scripted per step ("intake", "explain", "brief", "writeup"): the live classes identify their step
by the exact system prompt in app/ai/prompts.py. An item in a script is one of:
  - a dict or list  -> returned as JSON text in one text block
  - a str           -> returned as the raw text of the block (use for malformed JSON)
  - an Exception    -> raised
  - a response made by refusal(), truncated(), empty(), text_response()
  - a callable(kwargs) returning any of the above (lets a test answer from the prompt itself)
The last item of a script repeats, so one item covers any number of calls.
A step with no script raises UnscriptedCall, which the live code treats like any failure.
"""
import json
import re
from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any


class UnscriptedCall(Exception):
    pass


def text_response(payload: Any, stop_reason: str = "end_turn"):
    text = payload if isinstance(payload, str) else json.dumps(payload)
    return SimpleNamespace(content=[SimpleNamespace(type="text", text=text)], stop_reason=stop_reason)


def refusal():
    return SimpleNamespace(content=[], stop_reason="refusal")


def truncated(partial: str = '{"verdict": "career_pro'):
    return text_response(partial, stop_reason="max_tokens")


def empty():
    return SimpleNamespace(content=[], stop_reason="end_turn")


def timeout():
    return TimeoutError("request timed out")


def _flatten(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(_flatten(v) for v in value)
    if isinstance(value, dict):
        return _flatten(value.get("text", "")) if "text" in value else _flatten(list(value.values()))
    return str(getattr(value, "text", value))


def step_of(kwargs: dict) -> str:
    from app.ai import prompts

    system = _flatten(kwargs.get("system", ""))
    for name, prompt in (
        ("intake", prompts.INTAKE_SYSTEM),
        ("explain", prompts.EXPLAIN_SYSTEM),
        ("brief", prompts.BRIEF_SYSTEM),
        ("writeup", prompts.WRITEUP_SYSTEM),
    ):
        if system == prompt:
            return name
    return "unknown"


@dataclass
class Call:
    kwargs: dict
    step: str

    @property
    def system_text(self) -> str:
        return _flatten(self.kwargs.get("system", ""))

    @property
    def user_text(self) -> str:
        return "\n".join(_flatten(m.get("content", "")) for m in self.kwargs.get("messages", []))

    @property
    def prompt_text(self) -> str:
        """Everything the model was shown: system, messages and the output schema."""
        return "\n".join([self.system_text, self.user_text, json.dumps(self.kwargs.get("output_config", {}))])


@dataclass
class FakeAnthropic:
    scripts: dict[str, list] = field(default_factory=dict)
    calls: list[Call] = field(default_factory=list)

    def __post_init__(self):
        self.messages = SimpleNamespace(create=self._create)

    def script(self, step: str, *items):
        self.scripts[step] = list(items)
        return self

    def script_all(self, item):
        for step in ("intake", "explain", "brief", "writeup"):
            self.script(step, item)
        return self

    def calls_for(self, step: str) -> list[Call]:
        return [c for c in self.calls if c.step == step]

    def _create(self, **kwargs):
        call = Call(kwargs, step_of(kwargs))
        self.calls.append(call)
        queue = self.scripts.get(call.step)
        if not queue:
            raise UnscriptedCall(call.step)
        item = queue.pop(0) if len(queue) > 1 else queue[0]
        if callable(item) and not isinstance(item, Exception):
            item = item(kwargs)
        if isinstance(item, BaseException):
            raise item
        if isinstance(item, (dict, list, str)):
            return text_response(item)
        return item


# ---- canned model answers (one place to adapt if the JSON schemas change) ----

def intake_answer(verdict="career_problem", *, topic="none", summary="Wants product management help in fintech.",
                  domains=("Product Management",), sectors=("Fintech",), tools=(), wants_ai=False, question=""):
    return {"verdict": verdict, "sensitive_topic": topic, "summary": summary, "domains": list(domains),
            "sectors": list(sectors), "tools": list(tools), "wants_ai": wants_ai, "question": question}


def explain_answer(*matches):
    """matches: (mentor_id, [(field, value, text), ...])"""
    return {"matches": [{"mentor_id": mid, "reasons": [{"field": f, "value": v, "text": t} for f, v, t in rs]}
                        for mid, rs in matches]}


def writeup_answer(discussed=(), work_on=(), next_steps=()):
    """Each item: (text, quote)."""
    def items(pairs):
        return [{"text": t, "quote": q} for t, q in pairs]
    return {"discussed": items(discussed), "work_on": items(work_on), "next_steps": items(next_steps)}


_ID_RE = re.compile(r'"mentor_id":\s*"(M\d+)"')


def echo_explainer(mentors_by_id: dict):
    """A well behaved model: picks the first 3 candidate ids in the prompt and cites their domain."""
    def respond(kwargs):
        ids = list(dict.fromkeys(_ID_RE.findall(_flatten(kwargs["messages"]))))[:3]
        return explain_answer(*[
            (i, [("domain", mentors_by_id[i]["domain"], f"Their main area is {mentors_by_id[i]['domain']}.")])
            for i in ids
        ])
    return respond


def good_model(mentors_by_id: dict, notes_quote: str = "one page spec"):
    """A scripted model that behaves well on every step."""
    fake = FakeAnthropic()
    fake.script("intake", intake_answer())
    fake.script("explain", echo_explainer(mentors_by_id))
    fake.script("brief", {"brief": "The student wants help with product management in fintech."})
    fake.script("writeup", writeup_answer(discussed=[("Moving from ops into product.", "moving from ops into product")],
                                          next_steps=[("Draft a one page spec.", notes_quote)]))
    return fake
