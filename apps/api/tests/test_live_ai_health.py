"""GET /api/health reports live only when a key is set and USE_LIVE_AI is not 0."""
import sys

import pytest
from fastapi.testclient import TestClient


def health(monkeypatch, db_path, **env):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("USE_LIVE_AI", raising=False)
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    for name in [m for m in sys.modules if m == "app" or m.startswith("app.")]:
        del sys.modules[name]
    from app.main import app

    with TestClient(app) as c:
        r = c.get("/api/health")
    assert r.status_code == 200
    return r.json()


@pytest.mark.parametrize("env,expected", [
    ({"OPENROUTER_API_KEY": "sk-test"}, "live"),
    ({"OPENROUTER_API_KEY": "sk-test", "USE_LIVE_AI": "1"}, "live"),
    ({"OPENROUTER_API_KEY": "sk-test", "USE_LIVE_AI": "0"}, "fallback"),
    ({}, "fallback"),
    ({"USE_LIVE_AI": "1"}, "fallback"),
    ({"OPENROUTER_API_KEY": ""}, "fallback"),
    ({"OPENROUTER_API_KEY": "   "}, "fallback"),
])
def test_health_ai_mode(monkeypatch, db_path, env, expected):
    assert health(monkeypatch, db_path, **env) == {"ok": True, "ai": expected}
