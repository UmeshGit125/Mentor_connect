from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.fake import FakeMatchExplainer
from app.deps import AiServices
from app.errors import not_found
from app.matching.retrieve import top_candidates
from app.matching.verify import MAX_MATCHES, verify_matches
from app.matching.vocabulary import build_vocabulary
from app.models import ChatSession, Mentor, Message, Student
from app.schemas import ChatHistory, ChatMessage, ChatReply, Match, Need, PublicMentor

MAX_CLARIFY_TURNS = 3

CLARIFY_QUESTIONS = [
    "Happy to help. What kind of role or field are you aiming for, and what is the main thing "
    "you are stuck on?",
    "Thanks. Which industry or sector interests you most, and do you use any tools such as "
    "Jira, Excel or Mixpanel?",
    "One last question: is there a particular skill, such as marketing, product, sales or AI, "
    "that you want to grow?",
]
NO_MATCH_MESSAGE = (
    "I could not find a mentor in our list who fits that. Our mentors cover product, marketing, "
    "growth, sales, venture capital, data and AI across sectors like fintech, edtech and SaaS. "
    "The Mesa team has noted your request."
)
OFF_TOPIC_MESSAGE = (
    "I can only help with career questions and finding a mentor. If you tell me the role or "
    "field you want to grow in, I will suggest mentors."
)
SENSITIVE_MESSAGES = {
    "self_harm": (
        "I am really sorry you are going through this. You deserve support from a person right "
        "now. Please contact your local emergency number, or a helpline such as Tele-MANAS "
        "(14416 in India), or someone you trust. I cannot help with this here, and a mentor "
        "is not the right place for it."
    ),
    "mental_health": (
        "Thank you for sharing that. This is best handled by a qualified counsellor or "
        "therapist, not a career mentor. Please reach out to one, or to someone you trust. "
        "When you are ready, I am happy to help with career questions."
    ),
    "medical": (
        "I cannot help with medical questions. Please speak to a doctor. I am happy to help "
        "with career questions whenever you are ready."
    ),
    "legal": (
        "I cannot give legal advice. Please speak to a qualified lawyer. I am happy to help "
        "with career questions whenever you are ready."
    ),
}


def _public_mentors(db: Session) -> list[PublicMentor]:
    rows = db.scalars(select(Mentor).order_by(Mentor.id))
    return [PublicMentor.model_validate(m) for m in rows]


def final_matches(ai: AiServices, need: Need, candidates: list[PublicMentor]) -> list[Match]:
    """The mentors shown are the top candidates by score, in score order. The model only writes
    the reasons. When its reasons for a mentor fail verification, or it leaves a mentor out, the
    reasons come from the overlap rules instead, so a model cannot hide the right mentor."""
    asked = ai.explainer.explain(need, candidates)
    from_model = {m.mentor.id: m for m in verify_matches(asked, candidates)}
    rules = FakeMatchExplainer().explain(need, candidates)
    from_rules = {m.mentor.id: m for m in verify_matches(rules, candidates, len(candidates))}
    chosen = (from_model.get(c.id) or from_rules.get(c.id) for c in candidates)
    return [m for m in chosen if m is not None][:MAX_MATCHES]


def _session_for(db: Session, student: Student, session_id: str | None) -> ChatSession:
    if session_id is None:
        session = ChatSession(student_id=student.id)
        db.add(session)
        db.flush()
        return session
    session = db.get(ChatSession, session_id)
    if session is None or session.student_id != student.id:
        raise not_found("We could not find that chat.")
    return session


def _decide(db: Session, ai: AiServices, session: ChatSession, texts: list[str]) -> ChatReply:
    def reply(kind, message, matches=None, need=None) -> ChatReply:
        return ChatReply(
            session_id=session.id, kind=kind, message=message, matches=matches or [], need=need
        )

    mentors = _public_mentors(db)
    result = ai.intake.analyze(texts, build_vocabulary(mentors))
    if result.verdict == "sensitive":
        return reply("redirect", SENSITIVE_MESSAGES[result.topic or "mental_health"])
    if result.verdict == "off_topic":
        return reply("redirect", OFF_TOPIC_MESSAGE)

    if result.verdict == "vague":
        if session.clarify_count < MAX_CLARIFY_TURNS:
            question = result.question or CLARIFY_QUESTIONS[session.clarify_count]
            session.clarify_count += 1
            return reply("clarify", question)
        need = Need(summary=" ".join(" ".join(texts).split())[:140])
        return reply("no_match", NO_MATCH_MESSAGE, need=need)

    need = result.need or Need(summary=texts[-1][:140])
    candidates = [c.mentor for c in top_candidates(mentors, need)]
    matches = final_matches(ai, need, candidates) if candidates else []
    if not matches:
        return reply("no_match", NO_MATCH_MESSAGE, need=need)
    session.ever_matched = True
    count = len(matches)
    message = (
        f"Here {'is a mentor' if count == 1 else f'are {count} mentors'} who fit what you "
        "described. Each reason comes straight from their profile."
    )
    return reply("matches", message, matches, need)


def handle_chat(
    db: Session, ai: AiServices, student: Student, session_id: str | None, text: str
) -> ChatReply:
    session = _session_for(db, student, session_id)
    db.add(Message(session_id=session.id, role="student", text=text))
    db.flush()
    db.refresh(session)
    texts = [m.text for m in session.messages if m.role == "student"]

    chat_reply = _decide(db, ai, session, texts)

    db.add(Message(session_id=session.id, role="assistant", text=chat_reply.message))
    session.last_kind = chat_reply.kind
    session.last_reply = chat_reply.model_dump(mode="json")
    if chat_reply.need is not None:
        session.need = chat_reply.need.model_dump()
    db.commit()
    return chat_reply


def chat_history(db: Session, session_id: str) -> ChatHistory:
    session = db.get(ChatSession, session_id)
    if session is None:
        raise not_found("We could not find that chat.")
    return ChatHistory(
        messages=[ChatMessage(role=m.role, text=m.text) for m in session.messages],
        last=ChatReply.model_validate(session.last_reply) if session.last_reply else None,
    )
