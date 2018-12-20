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

import pytest
import responses
from tests.sampledata import record_set_values
from src.vinyldns.client import VinylDNSClient


def get_rs_type(rs):
    return rs.type


@pytest.fixture(scope="module", params=record_set_values, ids=get_rs_type)
def record_set(request):
    return request.param


@pytest.fixture(scope="module")
def mocked_responses():
    with responses.RequestsMock() as rsps:
        yield rsps


@pytest.fixture(scope="module")
def vinyldns_client():
    return VinylDNSClient('http://test.com', 'ok', 'ok')
