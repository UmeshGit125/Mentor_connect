# ruff: noqa: E501
"""Shared fixtures. Every test gets a fresh SQLite file and a freshly imported app.

DATABASE_URL and ADMIN_PASSWORD are set BEFORE `app` is imported, and any
previously imported `app*` modules are dropped so no engine or state leaks
between tests.
"""
import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

ADMIN_PASSWORD = "test-admin-pw"


def pytest_configure(config):
    config.addinivalue_line("markers", "live_ai: needs a real model key; skipped unless RUN_LIVE_AI=1")


def pytest_collection_modifyitems(config, items):
    if os.environ.get("RUN_LIVE_AI") == "1":
        return
    skip = pytest.mark.skip(reason="live_ai tests are skipped by default (set RUN_LIVE_AI=1)")
    for item in items:
        if "live_ai" in item.keywords:
            item.add_marker(skip)


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "test.db"


@pytest.fixture
def client(db_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("ADMIN_PASSWORD", ADMIN_PASSWORD)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    for name in [m for m in sys.modules if m == "app" or m.startswith("app.")]:
        del sys.modules[name]
    from app.main import app  # imported only after env is set

    with TestClient(app) as c:  # `with` runs startup (create tables, seed)
        yield c


@pytest.fixture
def admin_headers():
    return {"X-Admin-Password": ADMIN_PASSWORD}


@pytest.fixture
def mentors_by_id(client):
    return {m["id"]: m for m in client.get("/api/mentors").json()}


@pytest.fixture
def fake_ai(mentors_by_id):
    """A scripted Anthropic client. Tests add scripts with fake_ai.script(step, ...)."""
    from fake_anthropic import FakeAnthropic

    return FakeAnthropic()


@pytest.fixture
def live_api(client, fake_ai, monkeypatch):
    """The app with live mode on and every Live* class using the injected fake client."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("USE_LIVE_AI", "1")
    monkeypatch.delenv("OPENROUTER_MODEL", raising=False)
    from app import deps
    from app.ai import live

    services = deps.AiServices(
        "live",
        live.LiveIntakeAnalyzer(client=fake_ai),
        live.LiveMatchExplainer(client=fake_ai),
        live.LiveBriefWriter(client=fake_ai),
        live.LiveWriteupWriter(client=fake_ai),
    )
    client.app.dependency_overrides[deps.get_ai] = lambda: services
    return client
