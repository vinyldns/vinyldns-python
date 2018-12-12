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


class RecordType:
    A = "A"
    AAAA = "AAAA"
    CNAME = "CNAME"
    PTR = "PTR"
    MX = "MX"
    NS = "NS"
    SOA = "SOA"
    SRV = "SRV"
    TXT = "TXT"
    SSHFP = "SSHFP"
    SPF = "SPF"
    UNKNOWN = "UNKNOWN"


class RecordSetStatus:
    Active = "Active"
    Inactive = "Inactive"
    Pending = "Pending"
    PendingUpdate = "PendingUpdate"
    PendingDelete = "PendingDelete"


class AData(object):
    def __init__(self, address):
        self.address = address

    @staticmethod
    def from_dict(d):
        return AData(d['address'])


class AAAAData(object):
    def __init__(self, address):
        self.address = address

    @staticmethod
    def from_dict(d):
        return AAAAData(d['address'])


class CNAMEData(object):
    def __init__(self, cname):
        self.cname = cname

    @staticmethod
    def from_dict(d):
        return CNAMEData(d['cname'])


class MXData(object):
    def __init__(self, preference, exchange):
        self.preference = preference
        self.exchange = exchange

    @staticmethod
    def from_dict(d):
        return MXData(d['preference'], d['exchange'])


class NSData(object):
    def __init__(self, nsdname):
        self.nsdname = nsdname

    @staticmethod
    def from_dict(d):
        return NSData(d['nsdname'])


class PTRData(object):
    def __init__(self, ptrdname):
        self.ptrdname = ptrdname

    @staticmethod
    def from_dict(d):
        return PTRData(d['ptrdname'])


class SOAData(object):
    def __init__(self, mname, rname, serial, refresh, retry, expire, minimum):
        self.mname = mname
        self.rname = rname
        self.serial = serial
        self.refresh = refresh
        self.retry = retry
        self.expire = expire
        self.minimum = minimum

    @staticmethod
    def from_dict(d):
        return SOAData(d['mname'], d['rname'], d['serial'], d['refresh'], d['retry'], d['expire'], d['minimum'])


class SPFData(object):
    def __init__(self, text):
        self.text = text

    @staticmethod
    def from_dict(d):
        return SPFData(d['text'])


class SRVData(object):
    def __init__(self, priority, weight, port, target):
        self.priority = priority
        self.weight = weight
        self.port = port
        self.target = target

    @staticmethod
    def from_dict(d):
        return SRVData(d['priority'], d['weight'], d['port'], d['target'])


class SSHFPData(object):
    def __init__(self, algorithm, type, fingerprint):
        self.algorithm = algorithm
        self.type = type
        self.fingerprint = fingerprint

    @staticmethod
    def from_dict(d):
        return SSHFPData(d['algorithm'], d['type'], d['fingerprint'])


class TXTData(object):
    def __init__(self, text):
        self.text = text

    @staticmethod
    def from_dict(d):
        return TXTData(d['text'])


class UNKNOWNData(object):
    def __init__(self, rdata):
        self.rdata = rdata

    @staticmethod
    def from_dict(d):
        return UNKNOWNData(d['rdata'])


class RecordSet(object):
    # A mapping of record types to functions that create an RData instance from a dictionary
    rdata_converters = {
        RecordType.A: AData.from_dict,
        RecordType.AAAA: AAAAData.from_dict,
        RecordType.CNAME: CNAMEData.from_dict,
        RecordType.PTR: PTRData.from_dict,
        RecordType.MX: MXData.from_dict,
        RecordType.NS: NSData.from_dict,
        RecordType.SOA: SOAData.from_dict,
        RecordType.SRV: SRVData.from_dict,
        RecordType.TXT: TXTData.from_dict,
        RecordType.SSHFP: SSHFPData.from_dict,
        RecordType.SPF: SPFData.from_dict,
        RecordType.UNKNOWN: UNKNOWNData.from_dict
    }

    def __init__(self, zone_id, name, type, ttl, status=None, created=None, updated=None, records=[], id=None):
        self.zone_id = zone_id
        self.name = name
        self.type = type
        self.ttl = ttl
        self.status = status
        self.created = created
        self.updated = updated
        self.records = records
        self.id = id

    @staticmethod
    def from_dict(d):
        # Convert the array of rdata to instances, default to empty array if not present
        records = [RecordSet.rdata_converters[d['type']](rd) for rd in d.get('records', [])]
        return RecordSet(d['zoneId'], d['name'], d['type'], d['ttl'], d.get('status'), d.get('created'),
                         d.get('updated'), records, d.get('id'))

