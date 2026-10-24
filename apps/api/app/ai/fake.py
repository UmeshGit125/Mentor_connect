"""Deterministic stand-ins for the model: keyword and tag overlap, no network."""

import re

from app.ai.interface import IntakeResult, SensitiveTopic
from app.matching.retrieve import find_overlaps
from app.matching.vocabulary import Vocabulary
from app.schemas import Match, Need, PublicMentor, Reason, WriteupContent

# Career talk with few words and no known topic is too vague to match. Longer text is not vague.
VAGUE_MAX_WORDS = 7

SENSITIVE: dict[SensitiveTopic, list[str]] = {
    "self_harm": [
        "suicide",
        "suicidal",
        "kill myself",
        "end my life",
        "self harm",
        "self-harm",
        "hurt myself",
        "want to die",
        "no reason to live",
    ],
    "mental_health": [
        "depression",
        "depressed",
        "anxiety",
        "panic attack",
        "therapy",
        "therapist",
        "mental health",
        "counselling",
        "counseling",
    ],
    "medical": [
        "medical advice",
        "diagnosis",
        "medication",
        "symptoms",
        "prescription",
        "my doctor",
        "illness",
        "disease",
    ],
    "legal": [
        "lawyer",
        "lawsuit",
        "sue ",
        "legal advice",
        "court case",
        "attorney",
        "legal action",
    ],
}

DOMAIN_WORDS = {
    "Product Management": [
        "product manager",
        "product management",
        "product role",
        "roadmap",
        "apm",
    ],
    "Marketing": ["marketing", "brand", "seo", "content", "campaign"],
    "Growth": ["growth", "acquisition", "retention", "funnel"],
    "B2B Sales and Partnerships/CSM": [
        "sales",
        "customer success",
        "csm",
        "partnership",
        "partnerships",
        "b2b",
    ],
    "Venture Capital": ["venture capital", "vc", "investor", "investing"],
    "AI": ["ai", "artificial intelligence", "machine learning", "llm", "genai", "gen ai"],
    "Data": ["data", "analytics", "analyst", "sql"],
    "Category Management": ["category management", "category manager", "merchandising"],
    "Behavioural": [
        "behavioural",
        "behavioral",
        "soft skills",
        "communication skills",
    ],
    "Business Generalist": [
        "founder's office",
        "founders office",
        "chief of staff",
        "strategy",
        "generalist",
        "operations",
    ],
}
SECTOR_WORDS = {
    "Fintech": ["fintech", "payments", "banking"],
    "Edtech": ["edtech", "education"],
    "Healthtech": ["healthtech", "health tech", "healthcare"],
    "Medtech": ["medtech", "med tech"],
    "SaaS": ["saas"],
    "D2C": ["d2c", "direct to consumer"],
    "Quick Commerce": ["quick commerce", "quick-commerce", "q-commerce", "zepto", "blinkit"],
    "E-Commerce": ["ecommerce", "e-commerce", "ecomm"],
    "HRTech": ["hrtech", "hr tech", "hr-tech"],
    "Climatetech": ["climatetech", "climate tech", "greentech"],
    "Gaming": ["gaming"],
    "Media": ["media"],
    "Retail": ["retail"],
    "Manufacturing": ["manufacturing"],
    "Insurance": ["insurance"],
    "Consulting": ["consulting", "consultant", "consultancy"],
    "Agritech": ["agritech", "agriculture"],
    "Logistics": ["logistics", "supply chain"],
    "Delivery/Logistics": ["delivery logistics", "last mile"],
    "Travel Tech": ["travel tech", "traveltech"],
    "Sportstech": ["sportstech", "sports tech"],
    "Taxation": ["taxation", "tax"],
    "Employee Benefits": ["employee benefits"],
    "Food and Beverages": ["food and beverages", "food and beverage", "f&b"],
    "Mobility": ["mobility"],
    "Deeptech/AI": ["deeptech", "deep tech"],
    "Freelance": ["freelance", "freelancing"],
    "Accounting": ["accounting"],
    "VC": ["vc", "venture capital"],
    "IT": ["information technology"],
    "AI": ["ai", "artificial intelligence"],
}
TOOL_WORDS = {
    "Tableau": ["tableau"],
    "Hubspot": ["hubspot"],
    "Google Analytics": ["google analytics", "ga4"],
    "Jira": ["jira"],
    "Excel": ["excel"],
    "Mixpanel": ["mixpanel"],
    "n8n": ["n8n"],
    "Zapier": ["zapier"],
    "Langflow": ["langflow"],
}
DEFAULT_VOCABULARY = Vocabulary(tuple(DOMAIN_WORDS), tuple(SECTOR_WORDS), tuple(TOOL_WORDS))
MIN_OWN_NAME_CHARS = 4  # a short name such as "IT" is also an ordinary word, so it is not a keyword


def _table(
    known: dict[str, list[str]], values: tuple[str, ...], own_name: bool = True
) -> dict[str, list[str]]:
    """Keywords for each value in the mentor table. A value with no listed synonyms is matched by
    its own name, so a new value in the sheet can be asked for without editing this file."""
    table = {}
    for value in values:
        if value in known:
            table[value] = known[value]
        elif own_name and len(value) >= MIN_OWN_NAME_CHARS:
            table[value] = [value.casefold()]
    return table


AI_WORDS = ["ai", "llm", "genai", "gen ai", "automation", "automate", "agents", "chatgpt"]
CAREER_WORDS = [
    "career",
    "job",
    "mentor",
    "interview",
    "resume",
    "cv",
    "internship",
    "switch",
    "transition",
    "role",
    "startup",
    "skills",
    "hiring",
    "promotion",
    "founder",
    "company",
    "work",
]
OFF_TOPIC_WORDS = [
    "recipe",
    "weather",
    "joke",
    "poem",
    "movie",
    "song",
    "football",
    "cricket",
    "horoscope",
    "lyrics",
    "homework",
    "translate",
    "capital of",
    "stock price",
    "bitcoin price",
]
GREETINGS = ["hi", "hello", "hey", "help", "yo"]


# "not for the AI", "no sales", "without Excel", "instead of marketing": what the student rules out.
_NEGATED = re.compile(
    r"(?<![a-z0-9])(?:not|no|without|except|excluding|instead of|(?:do not|don't|dont) want)"
    r"\s+(?:for\s+|the\s+|any\s+|about\s+|in\s+)*[a-z0-9]+"
)


def _without_negated(text: str) -> str:
    """Removes what the student said they do not want, so its keywords are not read as a request."""
    return _NEGATED.sub(" ", text)


def _focus(messages: list[str]) -> list[str]:
    """A long latest message is a new request on its own, so earlier topics are dropped. A short
    one ("also fintech", "yes") is a follow-up, so the whole chat still counts."""
    if len(messages[-1].split()) <= VAGUE_MAX_WORDS:
        return messages
    return messages[-1:]


def _mentions(text: str, words: list[str]) -> bool:
    return any(re.search(rf"(?<![a-z0-9]){re.escape(w)}(?![a-z0-9])", text) for w in words)


def _hits(text: str, table: dict[str, list[str]]) -> list[str]:
    return [name for name, words in table.items() if _mentions(text, words)]


def _summary(
    domains: list[str], sectors: list[str], tools: list[str], wants_ai: bool, raw: str
) -> str:
    parts = [*domains, *sectors, *tools, *(["AI"] if wants_ai and "AI" not in domains else [])]
    if not parts:
        return " ".join(raw.split())[:140]
    return "Looking for a mentor in " + ", ".join(parts)


class FakeIntakeAnalyzer:
    def analyze(
        self, student_messages: list[str], vocabulary: Vocabulary | None = None
    ) -> IntakeResult:
        vocab = vocabulary or DEFAULT_VOCABULARY
        latest = student_messages[-1].casefold() if student_messages else ""
        for topic, phrases in SENSITIVE.items():
            if _mentions(latest, phrases):
                return IntakeResult("sensitive", topic=topic)

        student_messages = _focus(student_messages) if student_messages else student_messages
        text = _without_negated(" ".join(student_messages).casefold())
        domains = _hits(text, _table(DOMAIN_WORDS, vocab.domains))
        sectors = _hits(text, _table(SECTOR_WORDS, vocab.sectors))
        tools = _hits(text, _table(TOOL_WORDS, vocab.tools, own_name=False))
        wants_ai = _mentions(text, AI_WORDS)
        known = bool(domains or sectors or tools or wants_ai)
        need = Need(
            summary=_summary(domains, sectors, tools, wants_ai, " ".join(student_messages)),
            domains=domains,
            sectors=sectors,
            tools=tools,
            wants_ai=wants_ai,
        )
        if known:
            return IntakeResult("ok", need)
        short = len(text.split()) <= VAGUE_MAX_WORDS
        if _mentions(text, CAREER_WORDS):
            return IntakeResult("vague", None) if short else IntakeResult("ok", need)
        if _mentions(text, OFF_TOPIC_WORDS):
            return IntakeResult("off_topic")
        if _mentions(text, GREETINGS) and len(text.split()) <= 2:
            return IntakeResult("vague")
        # Unreadable or unsupported: nothing in the sheet can match, so say so.
        return IntakeResult("ok", need)


_REASON_TEXT = {
    "domain": "Their main area is {value}.",
    "roles": "They have worked in the role of {value}.",
    "sector": "They work in {value}.",
    "sectors": "They have experience in {value}.",
    "ai_tools": "They have worked with {value}.",
    "built_ai": "They have built an AI product, automation or workflow.",
    "tools": "They use {value}.",
}


class FakeMatchExplainer:
    def explain(self, need: Need, candidates: list[PublicMentor]) -> list[Match]:
        matches = []
        for mentor in candidates:
            reasons = [
                Reason(
                    field=o.field, value=o.value, text=_REASON_TEXT[o.field].format(value=o.value)
                )
                for o in find_overlaps(mentor, need)
                if o.field in _REASON_TEXT
            ][:3]
            # Quality only adds to a real reason. It is never the reason a mentor is shown.
            if reasons and mentor.quality == "Excellent" and len(reasons) < 3:
                reasons.append(
                    Reason(
                        field="quality", value="Excellent", text="Rated Excellent for mentorship."
                    )
                )
            if reasons:
                matches.append(Match(mentor=mentor, reasons=reasons))
        return matches


class FakeBriefWriter:
    def write(self, need: Need | None, student_messages: list[str]) -> str:
        said = " ".join(" ".join(student_messages).split())
        said = said if len(said) <= 600 else said[:597] + "..."
        topic = f"{need.summary}. " if need else ""
        return f'{topic}The student wrote: "{said}"'


_BULLET = re.compile(r"^\s*(?:[-*•]|\d+[.)])\s*")
_HEADINGS = {
    "discussed": "discussed",
    "we discussed": "discussed",
    "topics": "discussed",
    "work on": "work_on",
    "areas to work on": "work_on",
    "to improve": "work_on",
    "next steps": "next_steps",
    "next step": "next_steps",
    "action items": "next_steps",
}
_WORK_ON_WORDS = ["work on", "improve", "practice", "weak", "gap", "needs to", "focus on", "learn"]
_NEXT_WORDS = [
    "next step",
    "will ",
    "should ",
    "follow up",
    "reach out",
    "apply",
    "send ",
    "schedule",
    "plan to",
    "by next",
    "this week",
    "next week",
]


def _pieces(notes: str) -> list[str]:
    lines = [_BULLET.sub("", line).strip() for line in notes.splitlines()]
    pieces: list[str] = []
    for line in lines:
        pieces.extend(s.strip() for s in re.split(r"(?<=[.!?])\s+", line))
    return [p for p in pieces if p]


class FakeWriteupWriter:
    def write(self, notes: str) -> WriteupContent | None:
        if not notes.strip():
            return None
        buckets: dict[str, list[str]] = {"discussed": [], "work_on": [], "next_steps": []}
        current: str | None = None
        for piece in _pieces(notes):
            heading, _, rest = piece.partition(":")
            if heading.strip().casefold() in _HEADINGS:
                current = _HEADINGS[heading.strip().casefold()]
                piece = rest.strip()
                if not piece:
                    continue
            lowered = piece.casefold()
            if current:
                bucket = current
            elif _mentions(lowered, _NEXT_WORDS):
                bucket = "next_steps"
            elif _mentions(lowered, _WORK_ON_WORDS):
                bucket = "work_on"
            else:
                bucket = "discussed"
            buckets[bucket].append(piece)
        if not any(buckets.values()):
            return None  # nothing in the notes to report, so the write-up stays "none"
        return WriteupContent(**buckets)
