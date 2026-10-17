from pathlib import Path
import pytest


@pytest.fixture(scope="session")
def stack():
    # Imported here so unit tests that don't use the stack run without the harness installed.
    from openhost_test_harness import OpenhostStack

    with OpenhostStack(app_dir=Path(__file__).resolve().parent.parent) as s:
        yield s
