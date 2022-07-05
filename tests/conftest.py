import pytest
from .mockremote import MockRemote


@pytest.fixture
def remote():
    return MockRemote()
