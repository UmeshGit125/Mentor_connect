# ruff: noqa: E501
"""Cleaning of the sheet, observed through GET /mentors (50 mentors from 52 rows)."""
import json

import pytest
from helpers import PUBLIC_KEYS, P

JUNK = {"", "n/a", "na", "null", "none", "-", "not available", "nan"}


@pytest.fixture
def mentors(client):
    r = client.get(f"{P}/mentors")
    assert r.status_code == 200
    return {m["id"]: m for m in r.json()}


def test_deduped_to_50(client):
    ms = client.get(f"{P}/mentors").json()
    assert len(ms) == 50
    assert len({m["id"] for m in ms}) == 50
    assert [m["id"] for m in ms].count("M013") == 1
    assert [m["id"] for m in ms].count("M023") == 1


def test_public_shape_has_no_contact_fields(mentors):
    for m in mentors.values():
        assert set(m) == PUBLIC_KEYS, m["id"]
        assert set(m["tools"]) == {"tableau", "hubspot", "google_analytics", "jira", "excel", "mixpanel"}
    text = json.dumps(mentors).lower()
    for bad in ("@example.com", "(at)example", "linkedin.com", "mentor0", "+91", "00000 000"):
        # "mentor0" would catch emails like mentor003@; names are "Mentor 003" with a space
        assert bad not in text, bad


@pytest.mark.parametrize("mid,city", [
    ("M006", "Bengaluru"),   # BLR
    ("M037", "Bengaluru"),   # Bangalore, KA
    ("M024", "Bengaluru"),   # Bangalore
    ("M010", "Bengaluru"),   # bengaluru
    ("M003", "Bengaluru"),   # trailing space
    ("M038", "Mumbai"),      # Bombay
    ("M013", "Mumbai"),
    ("M030", "Canada"),      # kept as stated
    ("M048", "San Francisco"),
])
def test_city_normalised(mentors, mid, city):
    assert mentors[mid]["city"] == city


def test_delhi_variants_agree(mentors):
    assert mentors["M007"]["city"] == mentors["M004"]["city"]
    assert mentors["M007"]["city"] in ("Delhi", "New Delhi")


def test_city_na_is_null(mentors):
    assert mentors["M040"]["city"] is None


def test_no_duplicate_city_spellings(mentors):
    cities = {m["city"] for m in mentors.values() if m["city"]}
    assert len({c.lower() for c in cities}) == len(cities)
    for bad in ("BLR", "Bangalore", "Bangalore, KA", "Bombay", "bengaluru"):
        assert bad not in cities


@pytest.mark.parametrize("mid,expected", [
    ("M003", True),    # TRUE
    ("M030", True),    # Y
    ("M024", True),    # 1
    ("M031", True),    # YES
    ("M002", True),    # yes
    ("M009", False),   # No
    ("M007", False),   # FALSE
    ("M018", False),
    ("M039", None),    # blank
    ("M020", None),
])
def test_built_ai_boolean(mentors, mid, expected):
    assert mentors[mid]["built_ai"] is expected


def test_tool_booleans(mentors):
    assert mentors["M003"]["tools"]["tableau"] is True       # 'yes'
    assert mentors["M003"]["tools"]["jira"] is None          # blank
    t = mentors["M013"]["tools"]
    assert t["hubspot"] is True and t["google_analytics"] is True and t["jira"] is True  # 'Yes','1','Yes'
    assert t["tableau"] is None and t["excel"] is None and t["mixpanel"] is None


def test_junk_values_become_null(mentors):
    assert mentors["M029"]["company"] is None
    assert mentors["M029"]["sectors"] == []        # 'N/A'
    assert mentors["M029"]["quality"] is None      # 'null'
    assert mentors["M039"]["quality"] is None      # 'Not available'
    assert mentors["M035"]["quality"] is None      # 'N/A'
    for mid in ("M024", "M021", "M005", "M023", "M036"):   # 'N/A', '-', 'null', 'NA'
        assert mentors[mid]["seniority"] is None, mid
    assert mentors["M015"]["activities"] is None           # blank is not 0


def test_no_junk_strings_anywhere(mentors):
    def walk(v):
        if isinstance(v, str):
            yield v
        elif isinstance(v, list):
            for x in v:
                yield from walk(x)
        elif isinstance(v, dict):
            for x in v.values():
                yield from walk(x)

    for m in mentors.values():
        for s in walk({k: v for k, v in m.items() if k != "id"}):
            assert s == s.strip(), (m["id"], s)
            assert s.lower() not in JUNK, (m["id"], s)


def test_seniority_normalised(mentors):
    assert {m["seniority"] for m in mentors.values()} <= {"Mid-career", "Senior", None}
    for mid in ("M001", "M008", "M017", "M032"):
        assert mentors[mid]["seniority"] == "Senior", mid
    for mid in ("M039", "M009", "M045", "M012"):    # mid-career, Mid career, Mid-Career
        assert mentors[mid]["seniority"] == "Mid-career", mid


def test_domain_case_and_spacing(mentors):
    assert mentors["M013"]["domain"] == "Product Management"   # PRODUCT MANAGEMENT
    assert mentors["M015"]["domain"] == "Product Management"   # Product management
    assert mentors["M041"]["domain"] == "Marketing"            # ' Marketing'
    assert mentors["M036"]["domain"] == "Marketing"            # MARKETING
    assert mentors["M037"]["domain"] == "AI"                   # ' AI'
    domains = {m["domain"] for m in mentors.values()}
    assert len({d.lower() for d in domains}) == len(domains)


def test_activities_numeric(mentors):
    assert mentors["M030"]["activities"] == 3     # '3 activities'
    assert mentors["M012"]["activities"] == 2
    assert mentors["M036"]["activities"] == 0
    assert mentors["M010"]["activities"] == 7


def test_lists_split_cleanly(mentors):
    for m in mentors.values():
        for key in ("sectors", "roles", "ai_tools"):
            for item in m[key]:
                assert item and not any(sep in item for sep in (",", ";", "\n")), (m["id"], key, item)
    assert len(mentors["M007"]["sectors"]) == 4            # newline separated
    assert len(mentors["M036"]["sectors"]) == 4            # comma separated
    assert "Marketing" in mentors["M036"]["roles"]
    assert len(mentors["M036"]["roles"]) == 3
    assert mentors["M036"]["ai_tools"][0].lower() == "n8n"


def test_no_email_phone_linkedin_in_any_public_mentor(client):
    text = client.get(f"{P}/mentors").text.lower()
    assert "@" not in text
    assert "linkedin.com" not in text
    assert "example.com" not in text
    for mid in ("M001", "M013", "M023", "M050"):
        t = client.get(f"{P}/mentors/{mid}").text.lower()
        assert "@" not in t and "linkedin.com" not in t
