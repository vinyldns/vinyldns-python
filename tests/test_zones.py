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

import json

from tests.sampledata import forward_zone
from src.vinyldns.serdes import to_json_string, from_json_string
from src.vinyldns.zone import Zone


def test_zone_serdes():
    s = to_json_string(forward_zone)
    print(json.dumps(s, indent=4))
    z = from_json_string(s, Zone.from_dict)

    assert z.name == forward_zone.name
    assert z.connection.primary_server == forward_zone.connection.primary_server
    assert all([a.__dict__ == b.__dict__ for a, b in zip(z.acl.rules, forward_zone.acl.rules)])
