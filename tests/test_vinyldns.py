# Copyright 2018 Comcast Cable Communications Management, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""TODO: Add module docstring."""

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
