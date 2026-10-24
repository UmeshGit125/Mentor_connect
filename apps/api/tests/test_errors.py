# ruff: noqa: E501
"""Every error uses {"error": {"code", "message"}} with the contract status, no stack traces."""

from helpers import ERROR_STATUS, P, hdr, make_student

TRACE_MARKERS = ("Traceback", 'File "', "sqlalchemy", "pydantic", ".py", "site-packages", "loc\":")


def check(r, status=None):
    body = r.json()
    assert set(body) == {"error"}, body
    err = body["error"]
    assert set(err) == {"code", "message"}, err
    assert err["code"] in ERROR_STATUS, err
    assert r.status_code == ERROR_STATUS[err["code"]], (r.status_code, err)
    if status:
        assert r.status_code == status
    assert err["message"].strip()
    for m in TRACE_MARKERS:
        assert m not in r.text, (m, r.text)


def test_error_responses_have_contract_shape(client):
    sid = make_student(client)
    h = hdr(sid)
    cases = [
        ("get", f"{P}/mentors/M999", {}, 404),
        ("get", f"{P}/mentors/M999/slots", {}, 404),
        ("get", f"{P}/m/bad-token", {}, 404),
        ("get", f"{P}/chat/nope", {"headers": h}, 404),
        ("get", f"{P}/bookings/nope", {"headers": h}, 404),
        ("post", f"{P}/bookings/nope/cancel", {"headers": h}, 404),
        ("post", f"{P}/m/bad/close", {"json": {"outcome": "completed"}}, 404),
        ("get", f"{P}/admin/summary", {}, 401),
        ("get", f"{P}/admin/summary", {"headers": {"X-Admin-Password": "bad"}}, 401),
        ("post", f"{P}/chat", {"json": {"message": ""}, "headers": h}, 422),
        ("post", f"{P}/chat", {"json": {"message": "x" * 2001}, "headers": h}, 422),
        ("post", f"{P}/chat", {"json": {}, "headers": h}, 422),
        ("post", f"{P}/students", {"json": {"name": "A", "email": "bad"}}, 422),
        ("post", f"{P}/bookings", {"json": {"mentor_id": 5}, "headers": h}, 422),
    ]
    for method, path, kwargs, status in cases:
        check(getattr(client, method)(path, **kwargs), status)


def test_malformed_json_is_validation_error(client):
    r = client.post(f"{P}/students", content=b"{not json", headers={"Content-Type": "application/json"})
    check(r, 422)
    r = client.post(f"{P}/chat", content=b"[1,2,3]", headers={"Content-Type": "application/json", **hdr(make_student(client))})
    check(r, 422)


def test_unknown_route_and_wrong_method(client):
    r = client.get(f"{P}/does-not-exist")
    assert r.status_code == 404
    check(r)
    r = client.delete(f"{P}/mentors")
    assert r.status_code in (404, 405)
    assert "Traceback" not in r.text and r.json().get("error", {}).get("message", "x")


def test_unexpected_server_error_is_not_a_stack_trace(client):
    # A nasty but valid-looking input must never produce a 500 with internals.
    for q in ("'; drop table mentors; --", "%", "\u0000", "a" * 5000):
        r = client.get(f"{P}/mentors", params={"q": q})
        assert r.status_code < 500, r.text[:200]
        assert "Traceback" not in r.text
