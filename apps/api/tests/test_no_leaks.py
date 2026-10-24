# ruff: noqa: E501
"""Walk every GET endpoint after a full scenario and look for contact data."""
from helpers import GIBBERISH, P, chat, hdr, make_student, mentor_token, new_booking

FORBIDDEN = ("@example.com", "linkedin.com", "(at)example")


def test_no_get_endpoint_leaks_contact_data(client, db_path, admin_headers):
    sid, b, reply = new_booking(client, 1)
    tok = mentor_token(b, db_path)
    client.post(f"{P}/m/{tok}/close", json={"outcome": "completed", "notes": "We covered metrics and a spec."})
    s2 = make_student(client, 2)
    chat(client, s2, GIBBERISH)
    mentors = client.get(f"{P}/mentors").json()

    paths = [f"{P}/health", f"{P}/mentors", f"{P}/mentors?q=fintech", f"{P}/mentors?city=Bengaluru"]
    paths += [f"{P}/mentors/{m['id']}" for m in mentors]
    paths += [f"{P}/mentors/{m['id']}/slots" for m in mentors[:10]]
    student_paths = [f"{P}/bookings", f"{P}/bookings/{b['id']}", f"{P}/bookings/{b['id']}/writeup",
                     f"{P}/chat/{reply['session_id']}"]
    for p in paths:
        r = client.get(p)
        assert r.status_code == 200, p
        low = r.text.lower()
        assert not any(f in low for f in FORBIDDEN), p
    for p in student_paths:
        low = client.get(p, headers=hdr(sid)).text.lower()
        assert not any(f in low for f in FORBIDDEN), p
    low = client.get(f"{P}/m/{tok}").text.lower()
    assert not any(f in low for f in FORBIDDEN) and "s1@students.test" not in low
    low = client.get(f"{P}/admin/summary", headers=admin_headers).text.lower()
    assert not any(f in low for f in FORBIDDEN)


def test_error_bodies_do_not_leak(client):
    low = client.get(f"{P}/mentors/M999").text.lower()
    assert not any(f in low for f in FORBIDDEN)
