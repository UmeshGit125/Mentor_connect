# ruff: noqa: E501
"""Live write-up and brief through the booking and mentor-link endpoints."""
import pytest
from fake_anthropic import FakeAnthropic, intake_answer, writeup_answer
from helpers import P, hdr, mentor_token, new_booking

NOTES = ("We discussed moving from ops into product and how to write a PRD. "
         "Next she should draft a one page spec and interview two PMs.")


@pytest.fixture
def booked(live_api, fake_ai, mentors_by_id, db_path):
    from fake_anthropic import echo_explainer

    fake_ai.script("intake", intake_answer())
    fake_ai.script("explain", echo_explainer(mentors_by_id))
    fake_ai.script("brief", {"brief": "The student wants product help."})
    sid, b, _ = new_booking(live_api)
    return sid, b, mentor_token(b, db_path)


def close(api, tok, notes=NOTES):
    return api.post(f"{P}/m/{tok}/close", json={"outcome": "completed", "notes": notes})


def get_writeup(api, sid, b):
    return api.get(f"{P}/bookings/{b['id']}/writeup", headers=hdr(sid)).json()


def test_valid_quotes_make_a_ready_writeup(live_api, fake_ai, booked):
    sid, b, tok = booked
    fake_ai.script("writeup", writeup_answer(
        discussed=[("You talked about moving from ops into product.", "moving from ops into product")],
        next_steps=[("Draft a one page spec.", "draft a one page spec"), ("Interview two PMs.", "interview two PMs")]))
    assert close(live_api, tok).json()["writeup_status"] == "ready"
    w = get_writeup(live_api, sid, b)
    assert w["status"] == "ready"
    assert w["discussed"] == ["You talked about moving from ops into product."]
    assert w["next_steps"] == ["Draft a one page spec.", "Interview two PMs."]


def test_empty_section_stays_empty(live_api, fake_ai, booked):
    sid, b, tok = booked
    fake_ai.script("writeup", writeup_answer(discussed=[("Moving into product.", "moving from ops into product")]))
    close(live_api, tok)
    w = get_writeup(live_api, sid, b)
    assert w["status"] == "ready" and w["work_on"] == [] and w["next_steps"] == []
    assert w["discussed"] == ["Moving into product."]


def test_invented_quote_is_dropped_but_valid_item_kept(live_api, fake_ai, booked):
    sid, b, tok = booked
    fake_ai.script("writeup", writeup_answer(
        discussed=[("You discussed salary negotiation.", "we negotiated a 40 percent raise"),
                   ("Moving into product.", "moving from ops into product")]))
    close(live_api, tok)
    w = get_writeup(live_api, sid, b)
    assert w["discussed"] == ["Moving into product."]
    assert "salary" not in str(w)


def test_only_invented_quotes_never_reach_the_student(live_api, fake_ai, booked):
    sid, b, tok = booked
    fake_ai.script("writeup", writeup_answer(discussed=[("You discussed salary negotiation.", "a quote that is not there")]))
    close(live_api, tok)
    assert "salary" not in str(get_writeup(live_api, sid, b))


def test_model_with_nothing_to_say_gives_status_none(live_api, fake_ai, booked):
    sid, b, tok = booked
    fake_ai.script("writeup", writeup_answer())
    close(live_api, tok)
    w = get_writeup(live_api, sid, b)
    assert w == {"status": "none", "discussed": [], "work_on": [], "next_steps": []}


@pytest.mark.parametrize("notes", ["   ", " \n\t  \n", ""])
def test_blank_notes_never_call_the_model(live_api, fake_ai, booked, notes):
    sid, b, tok = booked
    fake_ai.script("writeup", writeup_answer(discussed=[("x", "y")]))
    r = close(live_api, tok, notes)
    assert r.status_code == 200 and r.json()["writeup_status"] == "none"
    assert fake_ai.calls_for("writeup") == []


def test_blank_notes_added_later_never_call_the_model(live_api, fake_ai, booked):
    sid, b, tok = booked
    fake_ai.script("writeup", writeup_answer(discussed=[("x", "y")]))
    live_api.post(f"{P}/m/{tok}/close", json={"outcome": "completed"})
    assert live_api.post(f"{P}/m/{tok}/notes", json={"notes": "   \n "}).status_code == 422
    assert fake_ai.calls_for("writeup") == []


def test_writer_returns_none_for_whitespace_without_a_call():
    from app.ai.live import LiveWriteupWriter

    fake = FakeAnthropic()
    assert LiveWriteupWriter(client=fake).write(" \n\t") is None
    assert fake.calls == []


@pytest.mark.parametrize("failure", [RuntimeError("x"), TimeoutError(), "not json", {"discussed": "no"}])
def test_writeup_failure_falls_back_to_a_ready_writeup(live_api, fake_ai, booked, failure):
    sid, b, tok = booked
    fake_ai.script("writeup", failure)
    r = close(live_api, tok)
    assert r.status_code == 200, r.text
    w = get_writeup(live_api, sid, b)
    assert w["status"] == "ready"
    assert any(w[k] for k in ("discussed", "work_on", "next_steps"))


def test_brief_failure_falls_back_and_booking_succeeds(live_api, fake_ai, mentors_by_id):
    from fake_anthropic import echo_explainer

    fake_ai.script("intake", intake_answer())
    fake_ai.script("explain", echo_explainer(mentors_by_id))
    fake_ai.script("brief", RuntimeError("down"))
    _, b, _ = new_booking(live_api)
    assert b["brief"].strip()


def test_live_brief_is_used_and_capped(live_api, fake_ai, mentors_by_id):
    from fake_anthropic import echo_explainer

    fake_ai.script("intake", intake_answer())
    fake_ai.script("explain", echo_explainer(mentors_by_id))
    fake_ai.script("brief", {"brief": "word " * 300})
    _, b, _ = new_booking(live_api)
    assert 0 < len(b["brief"].split()) <= 80
