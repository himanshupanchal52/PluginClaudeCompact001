"""Shared test setup.

pytest imports conftest.py automatically for every test in this directory and
below. Anything decorated with @pytest.fixture here is available to a test just
by naming it as a parameter - there is no registration step and no constructor
injection to wire up.
"""

import pathlib

import pytest

FIXTURE_DIR = pathlib.Path(__file__).parent / "fixtures"


@pytest.fixture
def fixture_path():
    """Return a helper that maps a fixture filename to its absolute path.

    Used as::

        def test_something(fixture_path):
            series = read_usage_series(fixture_path("simple.jsonl"))
    """

    def _path(name: str) -> str:
        return str(FIXTURE_DIR / name)

    return _path
