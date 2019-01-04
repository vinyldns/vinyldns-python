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
import re

camel_pat = re.compile(r'([A-Z])')
under_pat = re.compile(r'_([a-z])')


def camel_to_underscore(name):
    """
    Given a string in camelCase, convert to snake_case
    :param name: The string to be converted
    :return: A String formatted in snake_case
    """
    return camel_pat.sub(lambda x: '_' + x.group(1).lower(), name)


def underscore_to_camel(name):
    """
    Given a string in snake_case, convert to camelCase
    :param name: The string to be converted
    :return: A String formatted in camelCase
    """
    return under_pat.sub(lambda x: x.group(1).upper(), name)


def to_dict(obj, cls=None):
    """
    Given an object, serializes all fields to a dictionary including nested objects.

    Converts the field names to camelCase along the way suitable for convention in the API
    :param obj: An object instance
    :param cls: The type of class, useful for recursion
    :return: A fully populated dictionary with field names converted to camelCase
    """
    from datetime import date, datetime
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, dict):
        data = {}
        for (k, v) in obj.items():
            # Runs a conversion of snake_case to camelCase to be compliant with the API
            data[underscore_to_camel(k)] = to_dict(v, cls)
        return data
    elif hasattr(obj, "_ast"):
        return to_dict(obj._ast())
    elif hasattr(obj, "__iter__") and not isinstance(obj, str):
        return [to_dict(v, cls) for v in obj]
    elif hasattr(obj, "__dict__"):
        data = dict([(underscore_to_camel(key), to_dict(value, cls))
                     for key, value in obj.__dict__.items()
                     if not callable(value) and not key.startswith('_')])
        if cls is not None and hasattr(obj, "__class__"):
            data[cls] = underscore_to_camel(obj.__class__.__name__)
        return data
    else:
        return obj


def from_json_string(s, object_hook):
    """
    Given the string as json, loads it into a nested dictionary and passes it into the object_ctor
    provided to yield an instance of the object
    :param s: A json formatted string
    :param object_hook: A function that takes a dictionary and yields a new object instance
    :return: A populated object instance generated from the object_ctor
    """
    import json
    d = json.loads(s)
    return object_hook(d)


def to_json_string(o):
    """
    Converts the object to json
    :param o: An object that can be serialized to json
    :return: A json formatted string representation of the object
    """
    import json
    return json.dumps(to_dict(o))


def map_option(v, f):
    """
    Applies the function f to the value if it is not None
    :param v: A value that maybe None
    :param f: A function that takes a single argument to apply to v
    :return: The result of applying f to v; None if v is None
    """
    if v:
        return f(v)
    else:
        return None


def parse_datetime(s):
    """
    Parses the iso formatted date from the string provided
    :param s: An iso date formatted string
    :return: A datetime
    """
    import dateutil.parser
    return dateutil.parser.parse(s)
