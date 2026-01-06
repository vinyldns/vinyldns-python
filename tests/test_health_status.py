# Copyright 2026 Comcast Cable Communications Management, LLC
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

import responses

from vinyldns.serdes import to_json_string


def test_ping(mocked_responses, vinyldns_client):
    mocked_responses.add(
        responses.GET, 'http://test.com/ping',
        body='PONG', status=200)

    assert vinyldns_client.ping() == 'PONG'


def test_health(mocked_responses, vinyldns_client):
    mocked_responses.add(
        responses.GET, 'http://test.com/health',
        body='OK', status=200)

    assert vinyldns_client.health() == 'OK'


def test_color(mocked_responses, vinyldns_client):
    mocked_responses.add(
        responses.GET, 'http://test.com/color',
        body='blue', status=200)

    assert vinyldns_client.color() == 'blue'


def test_metrics_prometheus(mocked_responses, vinyldns_client):
    mocked_responses.add(
        responses.GET, 'http://test.com/metrics/prometheus?name=foo&name=bar',
        body='metric 1', status=200)

    assert vinyldns_client.metrics_prometheus(['foo', 'bar']) == 'metric 1'


def test_status_get(mocked_responses, vinyldns_client):
    mocked_responses.add(
        responses.GET, 'http://test.com/status',
        body=to_json_string({
            'processingDisabled': False,
            'color': 'blue',
            'keyName': 'vinyldns.',
            'version': '0.21.3'
        }),
        status=200)

    status = vinyldns_client.get_status()
    assert status.processing_disabled is False
    assert status.color == 'blue'
    assert status.key_name == 'vinyldns.'
    assert status.version == '0.21.3'


def test_status_update(mocked_responses, vinyldns_client):
    mocked_responses.add(
        responses.POST, 'http://test.com/status?processingDisabled=true',
        body=to_json_string({
            'processingDisabled': True,
            'color': 'blue',
            'keyName': 'vinyldns.',
            'version': '0.21.3'
        }),
        status=200)

    status = vinyldns_client.update_status(True)
    assert status.processing_disabled is True
