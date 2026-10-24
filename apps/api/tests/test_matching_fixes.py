# ruff: noqa: E501
"""Regression tests for three matching faults found on 24 Oct 2026.

1. "Edtech" matched "Healthtech / Medtech" because it is a substring of "Medtech".
2. Two tool matches outscored the one real Data mentor, and tool matches could not be explained.
3. Mentors whose domain or sector was not in a fixed tag list (Behavioural, Consulting) could never match.
"""
import pytest
from helpers import P, chat, make_student

from app.ai.fake import FakeIntakeAnalyzer, FakeMatchExplainer
from app.ai.live import candidate_row, intake_schema
from app.matching.retrieve import find_overlaps, top_candidates
from app.matching.verify import verify_matches
from app.matching.vocabulary import build_vocabulary
from app.schemas import Match, Need, PublicMentor, Reason, Tools
from app.services.chat import final_matches


def mentor(id, domain="Marketing", sector=None, **kw):
    return PublicMentor(id=id, name=f"Mentor {id}", domain=domain, sector=sector, **kw)


# 1. Sector names are compared whole, never as substrings.

def test_edtech_does_not_match_medtech():
    medtech = mentor("M1", sector="Healthtech / Medtech")
    edtech = mentor("M2", sector="Edtech")
    need = Need(summary="x", sectors=["Edtech"])
    assert find_overlaps(medtech, need) == []
    assert [c.mentor.id for c in top_candidates([medtech, edtech], need)] == ["M2"]


def test_each_side_of_a_two_sector_cell_still_matches():
    both = mentor("M1", sector="Healthtech / Medtech")
    assert find_overlaps(both, Need(summary="x", sectors=["Medtech"]))
    assert find_overlaps(both, Need(summary="x", sectors=["Healthtech"]))


def test_domain_is_matched_by_whole_name_not_substring():
    # "AI" is not inside any of these, but "Data" must not match a domain that merely contains it.
    assert find_overlaps(mentor("M1", domain="Database Administration"), Need(summary="x", domains=["Data"])) == []
    two = mentor("M2", domain="Business Generalist, Growth")
    assert find_overlaps(two, Need(summary="x", domains=["Growth"]))
    assert find_overlaps(two, Need(summary="x", domains=["Business Generalist"]))


# 2. Domain outranks tools, and a tool match can be explained.

def test_one_domain_expert_outranks_two_tool_matches():
    tools = Tools(tableau=True, excel=True)
    tool_only = [mentor(f"M{i}", domain="Product Management", tools=tools) for i in range(1, 9)]
    expert = mentor("M99", domain="Data")
    need = Need(summary="x", domains=["Data"], tools=["Tableau", "Excel"])
    ranked = top_candidates([*tool_only, expert], need)
    assert ranked[0].mentor.id == "M99"
    assert "M99" in [c.mentor.id for c in ranked]


def test_tool_overlap_is_explained_with_the_tool_not_with_quality():
    m = mentor("M1", domain="Product Management", quality="Excellent", tools=Tools(tableau=True))
    need = Need(summary="x", tools=["Tableau"])
    matches = FakeMatchExplainer().explain(need, [m])
    assert [(r.field, r.value) for r in matches[0].reasons][0] == ("tools", "Tableau")
    assert verify_matches(matches, [m])


def test_quality_alone_is_never_a_reason():
    m = mentor("M1", quality="Excellent")
    only_quality = Match(mentor=m, reasons=[Reason(field="quality", value="Excellent", text="Rated Excellent.")])
    assert verify_matches([only_quality], [m]) == []


def test_a_tool_the_mentor_does_not_have_is_rejected():
    m = mentor("M1", tools=Tools(tableau=True, excel=False))
    fake = Match(mentor=m, reasons=[Reason(field="tools", value="Excel", text="They use Excel.")])
    assert verify_matches([fake], [m]) == []


def test_live_explainer_row_lists_only_tools_that_are_true():
    row = candidate_row(mentor("M1", tools=Tools(tableau=True, excel=False, google_analytics=True)))
    assert row["tools"] == ["Tableau", "Google Analytics"]


# 3. Tags come from the mentor table.

def table():
    return [
        mentor("M1", domain="Behavioural"),
        mentor("M2", domain="Business Generalist, Growth", sector="Healthtech / Medtech", sectors=["Consulting", "Other"]),
        mentor("M3", domain="Data", ai_tools=["n8n", "Other"], tools=Tools(jira=True)),
    ]


def test_vocabulary_is_read_from_mentors_and_skips_placeholders():
    v = build_vocabulary(table())
    assert {"Behavioural", "Business Generalist", "Growth", "Data"} == set(v.domains)
    assert {"Healthtech", "Medtech", "Consulting"} == set(v.sectors)
    assert {"Jira", "n8n"} == set(v.tools)


def test_live_schema_offers_exactly_the_mentor_tags():
    props = intake_schema(build_vocabulary(table()))["properties"]
    assert set(props["domains"]["items"]["enum"]) == {"Behavioural", "Business Generalist", "Growth", "Data"}
    assert "Consulting" in props["sectors"]["items"]["enum"]
    assert "Other" not in props["sectors"]["items"]["enum"]


def test_fallback_finds_a_value_that_only_the_sheet_has():
    v = build_vocabulary(table())
    result = FakeIntakeAnalyzer().analyze(["I need help with soft skills for interviews"], v)
    assert result.need and result.need.domains == ["Behavioural"]
    result = FakeIntakeAnalyzer().analyze(["I want to work in consulting"], v)
    assert result.need and result.need.sectors == ["Consulting"]


def test_fallback_only_tags_values_that_exist_in_the_table():
    only_data = build_vocabulary([mentor("M1", domain="Data")])
    result = FakeIntakeAnalyzer().analyze(["I want to get into marketing and fintech"], only_data)
    assert result.need is None or (result.need.domains == [] and result.need.sectors == [])


# End to end on the real cleaned sheet.

@pytest.fixture
def sid(client):
    return make_student(client)


def ids_of(reply):
    return [m["mentor"]["id"] for m in reply["matches"]]


def test_chat_edtech_returns_only_edtech_mentors(client, sid):
    reply = chat(client, sid, "I want to work in edtech").json()
    assert reply["kind"] == "matches"
    for m in reply["matches"]:
        mentor_row = client.get(f"{P}/mentors/{m['mentor']['id']}").json()
        assert "Edtech" in [mentor_row["sector"], *mentor_row["sectors"]], mentor_row
        assert "Medtech" not in (mentor_row["sector"] or "")


def test_chat_data_analyst_with_tools_shows_the_data_mentor_first(client, sid):
    reply = chat(client, sid, "I know Excel and Tableau and want to become a data analyst").json()
    assert reply["kind"] == "matches"
    first = reply["matches"][0]
    assert first["mentor"]["domain"] == "Data"
    assert all(r["field"] != "quality" or len(first["reasons"]) > 1 for r in first["reasons"])


def test_chat_soft_skills_reaches_behavioural_mentors(client, sid):
    reply = chat(client, sid, "I get nervous in interviews and want help with soft skills and communication").json()
    assert reply["kind"] == "matches"
    assert {m["mentor"]["domain"] for m in reply["matches"]} == {"Behavioural"}


def test_chat_consulting_reaches_consulting_mentors(client, sid):
    reply = chat(client, sid, "I want to work in consulting").json()
    assert reply["kind"] == "matches"
    for m in reply["matches"]:
        row = client.get(f"{P}/mentors/{m['mentor']['id']}").json()
        assert "Consulting" in [row["sector"], *row["sectors"]]


# The latest request wins, and "not for X" is respected.

def test_a_new_long_request_drops_earlier_topics():
    ai = "I am an AI engineer intern and want to understand the AI domain better to work well in it"
    saas = "I want to learn system design for SaaS enterprise solutions and how that dev work happens"
    result = FakeIntakeAnalyzer().analyze([ai, saas])
    assert result.need and "AI" not in result.need.domains and result.need.wants_ai is False
    assert result.need.sectors == ["SaaS"]


def test_a_short_follow_up_keeps_the_earlier_topic():
    result = FakeIntakeAnalyzer().analyze(["I want to move into product management", "also in fintech"])
    assert result.need and result.need.domains == ["Product Management"]
    assert result.need.sectors == ["Fintech"]


@pytest.mark.parametrize("text", [
    "I want to learn the SDE role, assign me a mentor for that, not for the AI",
    "I want mentors for software engineering without AI in the picture at all",
    "please find me someone for backend development, no AI mentors please, I do not want AI",
])
def test_ruling_something_out_does_not_ask_for_it(text):
    result = FakeIntakeAnalyzer().analyze([text])
    assert result.need is None or ("AI" not in result.need.domains and not result.need.wants_ai)


def test_negation_only_removes_what_was_ruled_out():
    result = FakeIntakeAnalyzer().analyze(["I want to get into marketing and not sales at a fintech company"])
    assert result.need and result.need.domains == ["Marketing"] and result.need.sectors == ["Fintech"]


def test_chat_sde_after_ai_and_saas_does_not_reuse_the_ai_mentors(client):
    sid = make_student(client)
    first = chat(client, sid, "I am an AI engineer intern and want to understand the AI domain better to work well in it").json()
    assert first["kind"] == "matches"
    reply = chat(client, sid, "I want to learn the SDE role, assign me a mentor for that, not for the AI", first["session_id"]).json()
    assert reply["kind"] == "no_match" and reply["matches"] == []


# The code, not the model, decides who is shown.

class _Explainer:
    def __init__(self, picks):
        self.picks = picks

    def explain(self, need, candidates):
        rows = {m.id: m for m in candidates}
        return [
            Match(mentor=rows[i], reasons=[Reason(field="domain", value=rows[i].domain, text="Their main area.")])
            for i in self.picks
        ]


class _Ai:
    def __init__(self, picks):
        self.explainer = _Explainer(picks)


def test_a_model_that_leaves_out_the_best_mentor_cannot_hide_them():
    best = mentor("M99", domain="Data")
    others = [mentor(f"M{i}", domain="Product Management", tools=Tools(tableau=True, excel=True)) for i in range(1, 6)]
    need = Need(summary="x", domains=["Data"], tools=["Tableau", "Excel"])
    cands = [c.mentor for c in top_candidates([*others, best], need)]
    shown = final_matches(_Ai(["M1"]), need, cands)  # the model names only M1
    assert shown[0].mentor.id == "M99"
    assert len(shown) == 3


def test_model_reasons_are_used_when_they_verify_and_rules_fill_the_rest():
    ms = [mentor(f"M{i}", domain="Marketing") for i in range(1, 5)]
    need = Need(summary="x", domains=["Marketing"])
    cands = [c.mentor for c in top_candidates(ms, need)]
    shown = final_matches(_Ai(["M2"]), need, cands)
    assert [m.mentor.id for m in shown] == ["M1", "M2", "M3"]  # score order, not the model's order
    assert next(m for m in shown if m.mentor.id == "M2").reasons[0].text == "Their main area."


# The live model sometimes writes "marketing" in its summary but leaves the tag empty.

class _StubClient:
    def __init__(self, answer):
        import json
        from types import SimpleNamespace

        text = json.dumps(answer)
        reply = SimpleNamespace(stop_reason="end_turn", content=[SimpleNamespace(type="text", text=text)])
        self.messages = SimpleNamespace(create=lambda **kw: reply)


def _intake(summary, **tags):
    return {"verdict": "career_problem", "sensitive_topic": "none", "summary": summary, "domains": [],
            "sectors": [], "tools": [], "wants_ai": False, "question": "", **tags}


def test_a_tag_named_in_the_models_summary_is_not_lost():
    from app.ai.live import LiveIntakeAnalyzer

    answer = _intake("The student wants to get into marketing at a SaaS company.", sectors=["SaaS"])
    result = LiveIntakeAnalyzer(client=_StubClient(answer)).analyze(["i wnat to get into markting at a saas compnay"])
    assert result.need.domains == ["Marketing"] and result.need.sectors == ["SaaS"]


def test_a_summary_that_names_nothing_adds_nothing():
    from app.ai.live import LiveIntakeAnalyzer

    answer = _intake("The student wants to become an underwater welder on oil rigs.")
    result = LiveIntakeAnalyzer(client=_StubClient(answer)).analyze(["I want to be an underwater welder, I used to do marketing"])
    assert result.need.domains == [] and result.need.sectors == []
