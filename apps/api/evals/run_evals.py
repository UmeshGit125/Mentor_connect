# ruff: noqa: E501
"""Scripted student conversations against the real model, through the app. Not part of pytest.

    cd apps/api && uv run python evals/run_evals.py

Needs OPENROUTER_API_KEY (USE_LIVE_AI must not be 0). Without a key it says so and exits 0.
Uses a throwaway SQLite database. Writes evals/last_run.json.
"""
import json
import os
import re
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
API_ROOT = HERE.parent
CONTACT = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+|linkedin\.com|(?<!\w)\+?\d(?:[\s().-]?\d){8,}(?!\w)", re.I)
P = "/api"


def load_cases() -> list[dict]:
    lines = (HERE / "cases.jsonl").read_text().splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def check_reply(reply: dict, raw: str, mentors: dict, case: dict) -> list[str]:
    """Returns a list of invariant violations for one chat reply."""
    problems = []
    if CONTACT.search(raw):
        problems.append(f"contact data in response: {CONTACT.search(raw).group()!r}")
    for text in case.get("forbid_text", []):
        if text.casefold() in raw.casefold():
            problems.append(f"forbidden text {text!r} in response")
    for pattern in case.get("forbid_regex", []):
        if re.search(pattern, reply["message"], re.I):
            problems.append(f"forbidden pattern {pattern!r} in message")
    if reply["kind"] == "matches" and not 1 <= len(reply["matches"]) <= 3:
        problems.append("matches count not 1 to 3")
    if reply["kind"] != "matches" and reply["matches"]:
        problems.append("matches present on a non-matches reply")
    for m in reply["matches"]:
        row = mentors.get(m["mentor"]["id"])
        if row is None:
            problems.append(f"mentor id {m['mentor']['id']} is not in the sheet")
            continue
        if m["mentor"]["id"] in case.get("forbid_ids", []):
            problems.append(f"forbidden mentor {m['mentor']['id']} recommended")
        if m["mentor"] != row:
            problems.append(f"{row['id']} row differs from the stored row")
        if not 1 <= len(m["reasons"]) <= 3:
            problems.append(f"{row['id']} has {len(m['reasons'])} reasons")
        for r in m["reasons"]:
            stored = row.get(r["field"])
            if stored in (None, [], ""):
                problems.append(f"{row['id']} reason cites blank field {r['field']}")
            elif r["value"] not in (stored if isinstance(stored, list) else [str(stored), str(stored).lower()]):
                problems.append(f"{row['id']} reason value {r['value']!r} != stored {stored!r}")
            if not r["text"].strip():
                problems.append(f"{row['id']} reason text is empty")
    return problems


def run_case(client, case: dict, mentors: dict, blank_seniority: str, n: int) -> dict:
    sid = client.post(f"{P}/students", json={"name": f"Eval {n}", "email": f"eval{n}@students.test"}).json()["id"]
    session, replies, problems = None, [], []
    for message in case["messages"]:
        message = message.replace("{BLANK_SENIORITY_MENTOR}", blank_seniority)
        body = {"message": message, **({"session_id": session} if session else {})}
        r = client.post(f"{P}/chat", json=body, headers={"X-Student-Id": sid})
        if r.status_code != 200:
            problems.append(f"HTTP {r.status_code}: {r.text[:120]}")
            break
        reply = r.json()
        session = reply["session_id"]
        replies.append(reply)
        problems += check_reply(reply, r.text, mentors, case)
    if replies:
        kinds = [x["kind"] for x in replies]
        if kinds[-1] not in case["expect_kinds"]:
            problems.append(f"final kind {kinds[-1]!r}, expected one of {case['expect_kinds']}")
        if "expect_first" in case and kinds[0] not in case["expect_first"]:
            problems.append(f"first kind {kinds[0]!r}, expected one of {case['expect_first']}")
    return {
        "id": case["id"],
        "passed": not problems,
        "problems": problems,
        "kinds": [x["kind"] for x in replies],
        "mentor_ids": [m["mentor"]["id"] for x in replies for m in x["matches"]],
        "last_message": replies[-1]["message"] if replies else None,
    }


def main() -> int:
    if not os.environ.get("OPENROUTER_API_KEY", "").strip():
        print("OPENROUTER_API_KEY is not set, so the evals were skipped. Export it and run again.")
        return 0
    if os.environ.get("USE_LIVE_AI", "1").strip() == "0":
        print("USE_LIVE_AI=0 means the model is off, so the evals were skipped.")
        return 0
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["DATABASE_URL"] = f"sqlite:///{tmp}/evals.db"
        sys.path.insert(0, str(API_ROOT))
        from fastapi.testclient import TestClient

        from app.main import app

        with TestClient(app) as client:
            mode = client.get(f"{P}/health").json()["ai"]
            mentors = {m["id"]: m for m in client.get(f"{P}/mentors").json()}
            blank = next(m["name"] for m in mentors.values() if m["seniority"] is None)
            results = [run_case(client, c, mentors, blank, i) for i, c in enumerate(load_cases())]
    width = max(len(r["id"]) for r in results)
    for r in results:
        print(f"{'PASS' if r['passed'] else 'FAIL'}  {r['id']:<{width}}  {'>'.join(r['kinds']) or '-'}")
        for p in r["problems"]:
            print(f"      - {p}")
    failed = sum(not r["passed"] for r in results)
    print(f"\nmode={mode}  {len(results) - failed}/{len(results)} passed")
    (HERE / "last_run.json").write_text(json.dumps(
        {"ran_at": datetime.now(UTC).isoformat(), "ai_mode": mode, "passed": len(results) - failed,
         "total": len(results), "results": results}, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
