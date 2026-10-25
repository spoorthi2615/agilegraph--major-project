import pytest
import os

@pytest.fixture(autouse=True)
def enable_anonymous_mode_for_legacy_tests(monkeypatch):
    """
    Ensure existing regression test suites pass without needing to be rewritten
    with synthetic Authorization headers. Dedicated auth tests in test_auth.py
    explicitly disable this to verify strict 401 and 403 behavior.
    """
    if "AGILEGRAPH_ALLOW_ANONYMOUS" not in os.environ:
        monkeypatch.setenv("AGILEGRAPH_ALLOW_ANONYMOUS", "1")
