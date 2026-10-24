# ruff: noqa: E501
from datetime import UTC

from helpers import PUBLIC_KEYS, P, assert_error, make_student


def test_health(client):
    r = client.get(f"{P}/health")
    assert r.status_code == 200
    assert r.json() == {"ok": True, "ai": "fallback"}


def test_list_and_get(client):
    ms = client.get(f"{P}/mentors").json()
    one = client.get(f"{P}/mentors/{ms[0]['id']}")
    assert one.status_code == 200
    assert one.json() == ms[0]
    assert set(one.json()) == PUBLIC_KEYS


def test_get_unknown_is_not_found(client):
    assert_error(client.get(f"{P}/mentors/M999"), "not_found")


def test_filter_domain(client):
    ms = client.get(f"{P}/mentors", params={"domain": "Product Management"}).json()
    assert 5 <= len(ms) < 50
    assert all(m["domain"] == "Product Management" for m in ms)


def test_filter_sector(client):
    ms = client.get(f"{P}/mentors", params={"sector": "Fintech"}).json()
    assert ms and len(ms) < 50
    assert all(m["sector"] == "Fintech" for m in ms)


def test_filter_city(client):
    ms = client.get(f"{P}/mentors", params={"city": "Bengaluru"}).json()
    assert len(ms) > 20
    assert all(m["city"] == "Bengaluru" for m in ms)
    assert client.get(f"{P}/mentors", params={"city": "Mumbai"}).json()


def test_filters_combine_and_empty(client):
    both = client.get(f"{P}/mentors", params={"city": "Bengaluru", "domain": "Marketing"}).json()
    assert all(m["city"] == "Bengaluru" and m["domain"] == "Marketing" for m in both)
    assert client.get(f"{P}/mentors", params={"domain": "Underwater Welding"}).json() == []


def test_search_q(client):
    ms = client.get(f"{P}/mentors", params={"q": "fintech"}).json()
    assert ms and len(ms) < 50


def test_search_cannot_reach_contact_fields(client):
    for q in ("example.com", "mentor003@example.com", "linkedin.com", "anon-mentor-003", "00000 00003"):
        r = client.get(f"{P}/mentors", params={"q": q})
        assert r.status_code == 200
        assert r.json() == [], q


def test_slots_open_and_in_next_7_days(client):
    from datetime import datetime, timedelta

    slots = client.get(f"{P}/mentors/M001/slots").json()
    assert slots
    now = datetime.now(UTC)
    for s in slots:
        assert s["mentor_id"] == "M001" and s["status"] == "open"
        start = datetime.fromisoformat(s["start"].replace("Z", "+00:00"))
        if start.tzinfo is None:
            start = start.replace(tzinfo=UTC)
        assert now - timedelta(minutes=5) <= start <= now + timedelta(days=7, minutes=5)
        assert s["end"] > s["start"]


def test_every_mentor_has_slots(client):
    for m in client.get(f"{P}/mentors").json():
        assert client.get(f"{P}/mentors/{m['id']}/slots").json(), m["id"]


def test_slots_unknown_mentor(client):
    assert_error(client.get(f"{P}/mentors/M999/slots"), "not_found")


def test_students_idempotent_on_email(client):
    a = client.post(f"{P}/students", json={"name": "Asha", "email": "asha@students.test"}).json()
    b = client.post(f"{P}/students", json={"name": "Asha", "email": "asha@students.test"}).json()
    assert a["id"] == b["id"]
    assert make_student(client, 2) != a["id"]


def test_students_validation(client):
    for body in ({}, {"name": "", "email": "a@b.co"}, {"name": "A", "email": "not-an-email"}, {"name": "A"}):
        assert_error(client.post(f"{P}/students", json=body), "validation_error")
