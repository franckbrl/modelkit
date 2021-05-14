import asyncio
import os

import pytest


def pytest_addoption(parser):
    parser.addoption("--skipslow", action="store_true", help="skip slow tests")


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--skipslow"):
        return
    skip_slow = pytest.mark.skip(reason="need --skipslow option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: mark test as slow to run")


@pytest.fixture(scope="session")
def event_loop(request):
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


def skip_unless(var, value):
    env = os.environ.get(var)
    return pytest.mark.skipif(env != value, reason=f"{var} is not {value}")
