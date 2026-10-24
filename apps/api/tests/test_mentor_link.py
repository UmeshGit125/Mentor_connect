# ruff: noqa: E501
import pytest
from helpers import P, assert_error, hdr, mentor_token, new_booking

NOTES = ("We discussed moving from ops into product, how to write a PRD, and which metrics matter "
         "for a lending product. Next she should draft a one page spec and interview two PMs.")


@pytest.fixture
def setup(client, db_path):
    sid, b, _ = new_booking(client)
    return sid, b, mentor_token(b, db_path)


def writeup(client, sid, b):
    r = client.get(f"{P}/bookings/{b['id']}/writeup", headers=hdr(sid))
    assert r.status_code == 200, r.text
    return r.json()


def test_token_view(client, setup):
    sid, b, tok = setup
    r = client.get(f"{P}/m/{tok}")
    assert r.status_code == 200
    body = r.json()
    assert body["booking"]["id"] == b["id"]
    assert body["student_name"] == "Student 1"
    assert body["booking"]["brief"].strip()
    assert "example.com" not in r.text and "s1@students.test" not in r.text


def test_tokens_unique_and_unguessable(client, db_path):
    toks = [mentor_token(new_booking(client, i)[1], db_path) for i in (1, 2)]
    assert toks[0] != toks[1]
    assert all(len(t) >= 16 for t in toks)


def test_unknown_token_is_not_found(client):
    assert_error(client.get(f"{P}/m/nope-not-a-token"), "not_found")
    assert_error(client.post(f"{P}/m/nope/close", json={"outcome": "completed"}), "not_found")
    assert_error(client.post(f"{P}/m/nope/notes", json={"notes": "hello"}), "not_found")


def test_close_completed_with_notes_gives_writeup(client, setup):
    sid, b, tok = setup
    r = client.post(f"{P}/m/{tok}/close", json={"outcome": "completed", "notes": NOTES})
    assert r.status_code == 200
    assert r.json()["status"] == "completed"
    assert r.json()["writeup_status"] in ("ready", "notes_received")
    w = writeup(client, sid, b)
    assert w["status"] in ("ready", "notes_received")
    if w["status"] == "ready":
        # Ready means at least one section has content. Sections the notes do not support stay empty.
        assert any(w[k] for k in ("discussed", "work_on", "next_steps"))
        for k in ("discussed", "work_on", "next_steps"):
            assert all(isinstance(x, str) and x.strip() for x in w[k])
        assert w["discussed"]
        assert w["work_on"] == []  # NOTES say nothing about what to improve, so no filler
    else:
        assert w["discussed"] == w["work_on"] == w["next_steps"] == []


@pytest.mark.parametrize("notes", ["   ", " \n\t  \n", None, ""])
def test_close_without_real_notes_never_generates_writeup(client, setup, notes):
    sid, b, tok = setup
    body = {"outcome": "completed"}
    if notes is not None:
        body["notes"] = notes
    r = client.post(f"{P}/m/{tok}/close", json=body)
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "completed"
    assert r.json()["writeup_status"] == "none"
    w = writeup(client, sid, b)
    assert w == {"status": "none", "discussed": [], "work_on": [], "next_steps": []}


def test_closing_twice_is_invalid_state(client, setup):
    _, b, tok = setup
    assert client.post(f"{P}/m/{tok}/close", json={"outcome": "completed", "notes": NOTES}).status_code == 200
    assert_error(client.post(f"{P}/m/{tok}/close", json={"outcome": "completed", "notes": NOTES}), "invalid_state")
    assert_error(client.post(f"{P}/m/{tok}/close", json={"outcome": "no_show"}), "invalid_state")


def test_no_show_path(client, setup):
    sid, b, tok = setup
    r = client.post(f"{P}/m/{tok}/close", json={"outcome": "no_show"})
    assert r.status_code == 200 and r.json()["status"] == "no_show"
    assert writeup(client, sid, b)["status"] == "none"
    assert_error(client.post(f"{P}/m/{tok}/close", json={"outcome": "no_show"}), "invalid_state")


def test_no_show_with_notes_never_writes_up(client, setup):
    sid, b, tok = setup
    client.post(f"{P}/m/{tok}/close", json={"outcome": "no_show", "notes": NOTES})
    assert writeup(client, sid, b)["status"] == "none"


def test_add_notes_later(client, setup):
    sid, b, tok = setup
    client.post(f"{P}/m/{tok}/close", json={"outcome": "completed"})
    assert writeup(client, sid, b)["status"] == "none"
    r = client.post(f"{P}/m/{tok}/notes", json={"notes": NOTES})
    assert r.status_code == 200, r.text
    assert r.json()["writeup_status"] in ("ready", "notes_received")
    assert writeup(client, sid, b)["status"] in ("ready", "notes_received")


def test_whitespace_notes_later_never_generate(client, setup):
    sid, b, tok = setup
    client.post(f"{P}/m/{tok}/close", json={"outcome": "completed"})
    r = client.post(f"{P}/m/{tok}/notes", json={"notes": "  \n "})
    assert r.status_code in (200, 422)
    assert writeup(client, sid, b)["status"] == "none"


def test_notes_before_close_is_invalid_state(client, setup):
    _, _, tok = setup
    assert_error(client.post(f"{P}/m/{tok}/notes", json={"notes": NOTES}), "invalid_state")


def test_notes_length_and_outcome_validation(client, setup):
    _, _, tok = setup
    assert_error(client.post(f"{P}/m/{tok}/close", json={"outcome": "completed", "notes": "a" * 8001}), "validation_error")
    assert_error(client.post(f"{P}/m/{tok}/close", json={"outcome": "banana"}), "validation_error")
    assert_error(client.post(f"{P}/m/{tok}/close", json={}), "validation_error")
    # nothing above changed state
    assert client.get(f"{P}/m/{tok}").json()["booking"]["status"] == "confirmed"


def test_8000_char_notes_accepted(client, setup):
    _, _, tok = setup
    r = client.post(f"{P}/m/{tok}/close", json={"outcome": "completed", "notes": ("a note " * 1200)[:8000]})
    assert r.status_code == 200, r.text
