import requests
import responses
import pytest
from vinyldns.client import *

@pytest.fixture
def mocked_responses():
    with responses.RequestsMock() as rsps:
        yield rsps

def test_ping(mocked_responses):
    mocked_responses.add(
        responses.GET, 'http://test.com/ping',
        body='ok', status=200)
    client = VinylDNSClient('http://test.com', 'ok', 'ok')
    r = client.ping()
    assert r == 'ok'
