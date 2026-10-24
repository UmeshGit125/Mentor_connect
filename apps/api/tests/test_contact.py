"""POST /api/contact: stores an enquiry, validates input, limits repeat senders."""

from helpers import P

GOOD = {"name": "Asha", "email": "asha@example.com", "message": "How do I book a mentor?"}


def test_contact_is_stored(client):
    r = client.post(f"{P}/contact", json=GOOD)
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "received" and body["id"]


def test_contact_rejects_bad_input(client):
    for bad in (
        {**GOOD, "name": "  "},
        {**GOOD, "email": "not-an-email"},
        {**GOOD, "message": ""},
        {**GOOD, "message": "x" * 4001},
        {"name": "A"},
    ):
        r = client.post(f"{P}/contact", json=bad)
        assert r.status_code == 422, bad
        assert r.json()["error"]["code"] == "validation_error"


def test_contact_rate_limit(client):
    codes = [client.post(f"{P}/contact", json=GOOD).status_code for _ in range(6)]
    assert codes[:5] == [201] * 5
    assert codes[5] == 429
    assert client.post(f"{P}/contact", json=GOOD).json()["error"]["code"] == "rate_limited"
