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


class SystemStatus(object):
    def __init__(self, processing_disabled, color=None, key_name=None, version=None):
        self.processing_disabled = processing_disabled
        self.color = color
        self.key_name = key_name
        self.version = version

    @staticmethod
    def from_dict(d):
        return SystemStatus(
            processing_disabled=d.get('processingDisabled'),
            color=d.get('color'),
            key_name=d.get('keyName'),
            version=d.get('version')
        )
