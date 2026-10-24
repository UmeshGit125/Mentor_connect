# ruff: noqa: E501
"""Live intake and match explanation through POST /api/chat, with a scripted model."""
import pytest
from fake_anthropic import (
    echo_explainer,
    empty,
    explain_answer,
    intake_answer,
    refusal,
    timeout,
    truncated,
)
from helpers import CLEAR_FINTECH, VAGUE, chat, make_student, matched_chat

LEGAL = "My employer fired me, can I sue them? I need legal advice"


@pytest.fixture
def sid(live_api):
    return make_student(live_api)


def good_explainer(fake_ai, mentors_by_id):
    fake_ai.script("explain", echo_explainer(mentors_by_id))


# ---- intake classification reaches the right chat kind ----

def test_career_problem_reaches_matches(live_api, sid, fake_ai, mentors_by_id):
    fake_ai.script("intake", intake_answer("career_problem"))
    good_explainer(fake_ai, mentors_by_id)
    reply = chat(live_api, sid, CLEAR_FINTECH).json()
    assert reply["kind"] == "matches" and 1 <= len(reply["matches"]) <= 3
    assert reply["need"]["domains"] == ["Product Management"]
    assert len(fake_ai.calls_for("intake")) == 1 and len(fake_ai.calls_for("explain")) == 1


def test_vague_reaches_clarify_with_model_question(live_api, sid, fake_ai):
    fake_ai.script("intake", intake_answer("vague", domains=(), sectors=(), question="Which field do you want to move into?"))
    reply = chat(live_api, sid, VAGUE).json()
    assert reply["kind"] == "clarify" and reply["matches"] == []
    assert reply["message"] == "Which field do you want to move into?"


def test_off_topic_reaches_redirect(live_api, sid, fake_ai):
    fake_ai.script("intake", intake_answer("off_topic", domains=(), sectors=()))
    reply = chat(live_api, sid, "Tell me a recipe for dal").json()
    assert reply["kind"] == "redirect" and reply["matches"] == []
    assert not fake_ai.calls_for("explain")


@pytest.mark.parametrize("topic,msg", [("legal", LEGAL), ("medical", "What medicine should I take for my back pain"),
                                       ("mental_health", "I feel very low and anxious about work"),
                                       ("self_harm", "I want to end my life")])
def test_sensitive_reaches_redirect_without_mentors(live_api, sid, fake_ai, topic, msg):
    fake_ai.script("intake", intake_answer("sensitive", topic=topic, domains=(), sectors=()))
    reply = chat(live_api, sid, msg).json()
    assert reply["kind"] == "redirect" and reply["matches"] == []
    assert not fake_ai.calls_for("explain")


def test_self_harm_is_never_matched_even_if_model_says_career(live_api, sid, fake_ai):
    fake_ai.script("intake", intake_answer("career_problem"))
    reply = chat(live_api, sid, "I want to end my life, I need a job").json()
    assert reply["kind"] == "redirect" and reply["matches"] == []


def test_clarify_limit_of_three_holds_with_live_intake(live_api, sid, fake_ai):
    fake_ai.script("intake", intake_answer("vague", domains=(), sectors=(), question="Tell me more?"))
    session, kinds = None, []
    for _ in range(6):
        reply = chat(live_api, sid, "not sure, general help", session).json()
        session = reply["session_id"]
        kinds.append(reply["kind"])
        if reply["kind"] != "clarify":
            break
    assert kinds == ["clarify", "clarify", "clarify", "no_match"], kinds


def test_gibberish_with_empty_need_is_no_match(live_api, sid, fake_ai):
    fake_ai.script("intake", intake_answer("career_problem", summary="Unclear request.", domains=(), sectors=()))
    fake_ai.script("explain", explain_answer())
    reply = chat(live_api, sid, "asdkjh qweoiu zxcmnb").json()
    assert reply["kind"] == "no_match" and reply["matches"] == []


# ---- the verifier sits between the model and the student ----

def run_with_explain(live_api, sid, fake_ai, build):
    """build(candidate_ids) -> explain answer."""
    fake_ai.script("intake", intake_answer())
    fake_ai.script("explain", lambda kw: build(__import__("re").findall(r'"mentor_id":\s*"(M\d+)"', kw["messages"][0]["content"])))
    return chat(live_api, sid, CLEAR_FINTECH).json()


def test_invented_mentor_id_is_dropped(live_api, sid, fake_ai, mentors_by_id):
    def build(ids):
        real = ids[0]
        d = mentors_by_id[real]["domain"]
        return explain_answer(("M999", [("domain", "Product Management", "Invented.")]),
                              (real, [("domain", d, f"Their main area is {d}.")]))
    reply = run_with_explain(live_api, sid, fake_ai, build)
    assert reply["kind"] == "matches"
    ids = [m["mentor"]["id"] for m in reply["matches"]]
    # The invented id never shows. The real mentors are still shown, in score order.
    assert "M999" not in ids and all(i in mentors_by_id for i in ids) and ids


def test_reason_citing_blank_field_drops_the_match(live_api, sid, fake_ai, mentors_by_id):
    """seniority is blank on most rows, so a reason for it has nothing behind it."""
    def build(ids):
        blank = next(i for i in ids if mentors_by_id[i]["seniority"] is None)
        ok = next((i for i in ids if i != blank), None)
        out = [(blank, [("seniority", "Senior", "They are a senior leader.")])]
        if ok:
            d = mentors_by_id[ok]["domain"]
            out.append((ok, [("domain", d, f"Their main area is {d}.")]))
        return explain_answer(*out)
    reply = run_with_explain(live_api, sid, fake_ai, build)
    for m in reply["matches"]:
        assert all(r["field"] != "seniority" for r in m["reasons"])
        assert mentors_by_id[m["mentor"]["id"]]["seniority"] is not None or all(r["field"] != "seniority" for r in m["reasons"])


def test_reason_with_changed_value_is_dropped(live_api, sid, fake_ai, mentors_by_id):
    def build(ids):
        a, b = ids[0], ids[1]
        db = mentors_by_id[b]["domain"]
        return explain_answer((a, [("domain", mentors_by_id[a]["domain"] + " Plus", "Altered value.")]),
                              (b, [("domain", db, f"Their main area is {db}.")]))
    reply = run_with_explain(live_api, sid, fake_ai, build)
    for m in reply["matches"]:
        stored = mentors_by_id[m["mentor"]["id"]]
        for r in m["reasons"]:
            assert r["value"] == stored[r["field"]] or r["value"] in stored[r["field"]]
    assert all(not r["value"].endswith(" Plus") for m in reply["matches"] for r in m["reasons"])


def test_model_returning_no_matches_still_shows_the_top_candidates(live_api, sid, fake_ai, mentors_by_id):
    """The model cannot hide mentors the scoring found. Their reasons then come from the rules."""
    reply = run_with_explain(live_api, sid, fake_ai, lambda ids: explain_answer())
    assert reply["kind"] == "matches" and 1 <= len(reply["matches"]) <= 3
    for m in reply["matches"]:
        assert m["mentor"] == mentors_by_id[m["mentor"]["id"]]


def test_all_invalid_output_never_shows_invented_data(live_api, sid, fake_ai, mentors_by_id):
    """Every model match is invalid. The live explainer then uses the fake explainer (spec: any
    unusable model output falls back), so the student gets only verified rows, never the model's."""
    reply = run_with_explain(live_api, sid, fake_ai, lambda ids: explain_answer(("M999", [("domain", "X", "Invented.")])))
    assert reply["kind"] in ("matches", "no_match")
    for m in reply["matches"]:
        assert m["mentor"] == mentors_by_id[m["mentor"]["id"]]
        for r in m["reasons"]:
            assert r["text"] != "Invented."


# ---- every kind of failure falls back and the endpoint still answers ----

FAILURES = {
    "exception": RuntimeError("boom"),
    "timeout": timeout(),
    "refusal": refusal(),
    "max_tokens": truncated(),
    "empty_content": empty(),
    "malformed_json": "{not json at all",
    "json_not_object": "[1, 2, 3]",
    "schema_violation": {"verdict": "banana"},
    "wrong_types": {"verdict": "career_problem", "summary": 5, "domains": "x", "wants_ai": "yes"},
}
STEPS = ["intake", "explain", "brief"]


@pytest.mark.parametrize("step", STEPS)
@pytest.mark.parametrize("name", FAILURES)
def test_failure_falls_back_and_chat_still_returns_valid_reply(live_api, sid, fake_ai, mentors_by_id, name, step):
    fake_ai.script("intake", intake_answer())
    fake_ai.script("explain", echo_explainer(mentors_by_id))
    failure = FAILURES[name]
    if step == "explain" and name == "schema_violation":
        failure = {"matches": "nope"}
    fake_ai.script(step, failure)
    r = chat(live_api, sid, CLEAR_FINTECH)
    assert r.status_code == 200, r.text
    reply = r.json()
    assert reply["kind"] == "matches" and 1 <= len(reply["matches"]) <= 3
    assert set(reply) == {"session_id", "kind", "message", "matches", "need"}
    assert reply["message"].strip()


@pytest.mark.parametrize("name", FAILURES)
def test_total_outage_still_answers_every_kind(live_api, fake_ai, name):
    fake_ai.script_all(FAILURES[name])
    sid = make_student(live_api)
    for msg, kinds in [(CLEAR_FINTECH, {"matches"}), (VAGUE, {"clarify"}), ("asdkjh qweoiu zxcmnb lkjpoi", {"no_match"}),
                       ("I want to end my life", {"redirect"})]:
        r = chat(live_api, sid, msg)
        assert r.status_code == 200, r.text
        assert r.json()["kind"] in kinds, (msg, r.json()["kind"])


def test_matched_chat_helper_works_in_live_mode(live_api, fake_ai, mentors_by_id):
    fake_ai.script("intake", intake_answer())
    fake_ai.script("explain", echo_explainer(mentors_by_id))
    assert matched_chat(live_api, make_student(live_api))["matches"]
