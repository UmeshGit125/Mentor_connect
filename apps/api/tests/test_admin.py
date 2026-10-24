# ruff: noqa: E501
from helpers import (
    GIBBERISH,
    VAGUE,
    P,
    assert_error,
    chat,
    hdr,
    make_student,
    mentor_token,
    move_slot_to_past,
    new_booking,
)

NOTES = "We discussed product roadmaps and metrics. Next steps: write a one page spec and share it."
URL = f"{P}/admin/summary"


def test_wrong_or_missing_password_is_unauthorized(client):
    assert_error(client.get(URL), "unauthorized")
    assert_error(client.get(URL, headers={"X-Admin-Password": "wrong"}), "unauthorized")
    assert_error(client.get(URL, headers={"X-Admin-Password": ""}), "unauthorized")


def test_empty_database_summary(client, admin_headers):
    r = client.get(URL, headers=admin_headers)
    assert r.status_code == 200
    s = r.json()
    assert s["funnel"] == {"chats_started": 0, "matched": 0, "booked": 0, "completed": 0,
                           "writeups_ready": 0, "rebooked": 0}
    assert s["bookings_by_status"] == {"confirmed": 0, "completed": 0, "no_show": 0, "cancelled": 0}
    assert s["stuck"] == [] and s["unmatched"] == []


def scripted(client, db_path):
    """3 chats (matched / no_match / clarify), 1 booking that is completed with notes."""
    sid, b, _ = new_booking(client, 1)
    tok = mentor_token(b, db_path)
    client.post(f"{P}/m/{tok}/close", json={"outcome": "completed", "notes": NOTES})
    s2 = make_student(client, 2)
    nm = chat(client, s2, GIBBERISH).json()
    s3 = make_student(client, 3)
    assert chat(client, s3, VAGUE).json()["kind"] == "clarify"
    return b, nm


def test_funnel_matches_scripted_scenario(client, db_path, admin_headers):
    b, _ = scripted(client, db_path)
    s = client.get(URL, headers=admin_headers).json()
    f = s["funnel"]
    assert f["chats_started"] == 3
    assert f["matched"] == 1
    assert f["booked"] == 1
    assert f["completed"] == 1
    assert f["writeups_ready"] in (0, 1)
    wu = client.get(f"{P}/bookings/{b['id']}/writeup", headers=hdr(b["student_id"])).json()["status"]
    assert f["writeups_ready"] == (1 if wu == "ready" else 0)
    assert f["rebooked"] == 0
    assert s["bookings_by_status"] == {"confirmed": 0, "completed": 1, "no_show": 0, "cancelled": 0}


def test_unmatched_contains_no_match_chat(client, db_path, admin_headers):
    _, nm = scripted(client, db_path)
    um = client.get(URL, headers=admin_headers).json()["unmatched"]
    assert [u["id"] for u in um] == [nm["session_id"]]
    assert um[0]["summary"].strip() and um[0]["created_at"]


def test_mentor_load(client, db_path, admin_headers):
    b, _ = scripted(client, db_path)
    sid2, b2, _ = new_booking(client, 4, mentor_id=b["mentor"]["id"], slot_index=1)
    load = {m["mentor_id"]: m for m in client.get(URL, headers=admin_headers).json()["mentor_load"]}
    row = load[b["mentor"]["id"]]
    assert row["active"] == 1 and row["completed"] == 1 and row["name"] == b["mentor"]["name"]


def test_stuck_bookings(client, db_path, admin_headers):
    _, stuck, _ = new_booking(client, 1)
    _, fresh, _ = new_booking(client, 2)
    sid3, done, _ = new_booking(client, 3)
    client.post(f"{P}/m/{mentor_token(done, db_path)}/close", json={"outcome": "no_show"})
    move_slot_to_past(db_path, stuck["slot"]["id"], days_ago=5)
    move_slot_to_past(db_path, done["slot"]["id"], days_ago=5)
    ids = [x["id"] for x in client.get(URL, headers=admin_headers).json()["stuck"]]
    assert ids == [stuck["id"]]
    assert fresh["id"] not in ids and done["id"] not in ids


def test_slot_ended_one_day_ago_is_not_stuck(client, db_path, admin_headers):
    _, b, _ = new_booking(client, 1)
    move_slot_to_past(db_path, b["slot"]["id"], days_ago=1)
    assert client.get(URL, headers=admin_headers).json()["stuck"] == []


def test_summary_has_no_contact_data(client, db_path, admin_headers):
    scripted(client, db_path)
    text = client.get(URL, headers=admin_headers).text.lower()
    assert "@" not in text and "linkedin.com" not in text
