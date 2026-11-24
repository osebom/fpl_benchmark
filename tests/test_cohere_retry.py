from fpl_sim.agents.cohere_agent import _is_rate_limit, _retry_after_seconds


class _RateLimit(Exception):
    def __init__(self, status_code=429, headers=None):
        self.status_code = status_code
        self.headers = headers or {}


def test_detects_429():
    assert _is_rate_limit(_RateLimit())
    assert not _is_rate_limit(RuntimeError("nope"))


def test_retry_after_header():
    assert _retry_after_seconds(_RateLimit(headers={"retry-after": "15"})) == 15.0
    assert _retry_after_seconds(_RateLimit()) is None
