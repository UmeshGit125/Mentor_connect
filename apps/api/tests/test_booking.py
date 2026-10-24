# ruff: noqa: E501
import threading

from helpers import P, assert_error, book, hdr, make_student, matched_chat, new_booking, open_slots


def test_happy_path(client):
    sid, b, reply = new_booking(client)
    assert b["status"] == "confirmed" and b["student_id"] == sid
    assert b["writeup_status"] == "none"
    assert b["brief"].strip()
    assert b["slot"]["mentor_id"] == b["mentor"]["id"]
    assert b["mentor"]["id"] in {m["mentor"]["id"] for m in reply["matches"]}
    got = client.get(f"{P}/bookings/{b['id']}", headers=hdr(sid))
    assert got.status_code == 200 and got.json()["id"] == b["id"]
    listing = client.get(f"{P}/bookings", headers=hdr(sid)).json()
    assert [x["id"] for x in listing] == [b["id"]]


def test_booked_slot_leaves_open_list(client):
    _, b, _ = new_booking(client)
    assert b["slot"]["id"] not in [s["id"] for s in open_slots(client, b["mentor"]["id"])]


def test_slot_taken_and_state_unchanged(client):
    _, b, _ = new_booking(client, 1)
    s2 = make_student(client, 2)
    reply = matched_chat(client, s2)
    r = book(client, s2, b["mentor"]["id"], b["slot"]["id"], reply["session_id"])
    assert_error(r, "slot_taken")
    assert client.get(f"{P}/bookings", headers=hdr(s2)).json() == []
    assert client.get(f"{P}/bookings/{b['id']}", headers=hdr(b["student_id"])).json()["status"] == "confirmed"


def test_concurrent_bookings_of_one_slot_give_exactly_one_success(client):
    n = 6
    reply0 = None
    students = []
    for i in range(1, n + 1):
        sid = make_student(client, i)
        reply = matched_chat(client, sid)
        reply0 = reply0 or reply
        students.append((sid, reply["session_id"]))
    mentor_id = reply0["matches"][0]["mentor"]["id"]
    slot_id = open_slots(client, mentor_id)[0]["id"]
    barrier = threading.Barrier(n)
    results = [None] * n

    def worker(i):
        sid, session = students[i]
        barrier.wait()
        results[i] = book(client, sid, mentor_id, slot_id, session)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    codes = sorted(r.status_code for r in results)
    assert codes == [201] + [409] * (n - 1), [r.text for r in results]
    for r in results:
        if r.status_code == 409:
            assert r.json()["error"]["code"] == "slot_taken"
    total = sum(len(client.get(f"{P}/bookings", headers=hdr(s)).json()) for s, _ in students)
    assert total == 1


def test_booking_cap_at_fourth_active_booking(client):
    sid = make_student(client)
    reply = matched_chat(client, sid)
    mentors = [m["id"] for m in client.get(f"{P}/mentors").json()][:4]
    made = []
    for mid in mentors[:3]:
        r = book(client, sid, mid, open_slots(client, mid)[0]["id"], reply["session_id"])
        assert r.status_code == 201, r.text
        made.append(r.json())
    r4 = book(client, sid, mentors[3], open_slots(client, mentors[3])[0]["id"], reply["session_id"])
    assert_error(r4, "booking_cap_reached")
    assert len(client.get(f"{P}/bookings", headers=hdr(sid)).json()) == 3
    # cancelling one frees capacity
    assert client.post(f"{P}/bookings/{made[0]['id']}/cancel", headers=hdr(sid)).status_code == 200
    r5 = book(client, sid, mentors[3], open_slots(client, mentors[3])[0]["id"], reply["session_id"])
    assert r5.status_code == 201, r5.text


def test_mentor_cap_reached_at_sixth_booking(client):
    mid = "M002"
    slots = open_slots(client, mid)
    assert len(slots) >= 6, "need at least 6 open slots per mentor in the seed to test the weekly cap"
    for i in range(1, 6):
        sid = make_student(client, i)
        reply = matched_chat(client, sid)
        r = book(client, sid, mid, slots[i - 1]["id"], reply["session_id"])
        assert r.status_code == 201, r.text
    sid = make_student(client, 6)
    reply = matched_chat(client, sid)
    assert_error(book(client, sid, mid, slots[5]["id"], reply["session_id"]), "mentor_cap_reached")
    assert client.get(f"{P}/bookings", headers=hdr(sid)).json() == []


def test_cancel_frees_slot(client):
    sid, b, _ = new_booking(client)
    r = client.post(f"{P}/bookings/{b['id']}/cancel", headers=hdr(sid))
    assert r.status_code == 200 and r.json()["status"] == "cancelled"
    assert b["slot"]["id"] in [s["id"] for s in open_slots(client, b["mentor"]["id"])]
    # another student can now take it
    s2 = make_student(client, 2)
    reply = matched_chat(client, s2)
    assert book(client, s2, b["mentor"]["id"], b["slot"]["id"], reply["session_id"]).status_code == 201


def test_cancel_twice_is_invalid_state(client):
    sid, b, _ = new_booking(client)
    client.post(f"{P}/bookings/{b['id']}/cancel", headers=hdr(sid))
    assert_error(client.post(f"{P}/bookings/{b['id']}/cancel", headers=hdr(sid)), "invalid_state")


def test_cancel_after_completion_is_invalid_state(client, db_path):
    from helpers import mentor_token

    sid, b, _ = new_booking(client)
    tok = mentor_token(b, db_path)
    assert client.post(f"{P}/m/{tok}/close", json={"outcome": "completed"}).status_code == 200
    assert_error(client.post(f"{P}/bookings/{b['id']}/cancel", headers=hdr(sid)), "invalid_state")


def test_other_students_booking_is_not_found(client):
    _, b, _ = new_booking(client, 1)
    other = make_student(client, 2)
    for path, method in ((f"/bookings/{b['id']}", "get"), (f"/bookings/{b['id']}/writeup", "get"),
                         (f"/bookings/{b['id']}/cancel", "post")):
        assert_error(getattr(client, method)(P + path, headers=hdr(other)), "not_found")
    assert client.get(f"{P}/bookings/{b['id']}", headers=hdr(b["student_id"])).json()["status"] == "confirmed"


def test_unknown_slot_and_mentor(client):
    sid = make_student(client)
    reply = matched_chat(client, sid)
    mid = reply["matches"][0]["mentor"]["id"]
    assert book(client, sid, mid, "no-such-slot", reply["session_id"]).status_code == 404
    slot = open_slots(client, mid)[0]
    assert book(client, sid, "M999", slot["id"], reply["session_id"]).status_code == 404


def test_slot_must_belong_to_mentor(client):
    sid = make_student(client)
    reply = matched_chat(client, sid)
    slot_of_other = open_slots(client, "M001")[0]
    r = book(client, sid, "M002", slot_of_other["id"], reply["session_id"])
    assert r.status_code in (404, 409, 422), r.text
    assert client.get(f"{P}/bookings", headers=hdr(sid)).json() == []


def test_booking_validation(client):
    sid = make_student(client)
    assert_error(client.post(f"{P}/bookings", json={}, headers=hdr(sid)), "validation_error")
