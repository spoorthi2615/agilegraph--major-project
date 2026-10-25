import os
import tempfile
import pytest

# Ensure all tests run against an isolated temporary SQLite database rather than local development state
_test_db_handle = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_test_db_path = _test_db_handle.name
_test_db_handle.close()
os.environ.setdefault("AGILEGRAPH_AUTH_DB", _test_db_path)

@pytest.fixture(scope="session", autouse=True)
def isolate_test_database():
    yield
    try:
        if os.path.exists(_test_db_path):
            os.remove(_test_db_path)
    except OSError:
        pass

@pytest.fixture(autouse=True)
def enable_anonymous_mode_for_legacy_tests(monkeypatch):
    """
    Ensure existing regression test suites pass without needing to be rewritten
    with synthetic Authorization headers. Dedicated auth tests in test_auth.py
    explicitly disable this to verify strict 401 and 403 behavior.
    """
    if "AGILEGRAPH_ALLOW_ANONYMOUS" not in os.environ:
        monkeypatch.setenv("AGILEGRAPH_ALLOW_ANONYMOUS", "1")
