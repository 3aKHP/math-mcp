import pytest


@pytest.fixture
def call_tool():
    """Helper: call a tool function directly and return its string result."""
    def _call(fn, **kwargs):
        return fn(**kwargs)
    return _call
