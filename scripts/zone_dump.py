import os
import json
import csv
import sys
from datetime import datetime
from vinyldns.client import VinylDNSClient

VINYLDNS_HOST = os.getenv("VINYLDNS_HOST")
VINYLDNS_ACCESS_KEY = os.getenv("VINYLDNS_ACCESS_KEY")
VINYLDNS_SECRET_KEY = os.getenv("VINYLDNS_SECRET_KEY")


def format_record_data(record_set, record):
    record_type = record_set.type

    formatters = {
        "A": lambda r: r.address,
        "AAAA": lambda r: r.address,
        "PTR": lambda r: r.ptrdname,
        "CNAME": lambda r: r.cname,
        "NS": lambda r: r.nsdname,
        "TXT": lambda r: r.text,
        "SPF": lambda r: r.text,
        "SRV": lambda r: (
            f"priority: {r.priority}, weight: {r.weight}, "
            f"target: {r.target}, port: {r.port}"
         ),
        "MX": lambda r: (
            f"preference: {r.preference}, exchange: {r.exchange}"
        ),
        "SOA": lambda r: (
            f"mname: {r.mname}, rname: {r.rname}, serial: {r.serial}, "
            f"refresh: {r.refresh}, retry: {r.retry}, expire: {r.expire}, "
            f"minimum: {r.minimum}"
        ),
        "SSHFPD": lambda r: (
            f"algorithm: {r.algorithm}, type: {r.type}, fingerprint: {r.fingerprint}"
        )
    }
    return formatters.get(record_type, lambda r: "unsupported record type")(record)


def dump_zone_records(client, zone_name):
    zone = client.get_zone_by_name(zone_name)
    all_records = []
    next_id = None

    while True:
        response = client.list_record_sets(zone.id, start_from=next_id)
        for record_set in response.record_sets:
            for record in record_set.records:
                record_info = {
                    "fqdn": record_set.fqdn,
                    "type": record_set.type,
                    "record_data": format_record_data(record_set, record)
                }
                all_records.append(record_info)
        next_id = response.next_id
        if not next_id:
            break

    return all_records


def write_records_to_csv(records, zone_name, output_dir="output"):
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_zone_name = zone_name.rstrip('.').replace('.', '_')
    filename = f"{safe_zone_name}_records_{timestamp}.csv"
    filepath = os.path.join(output_dir, filename)

    fieldnames = {key for record in records for key in record.keys()}
    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow(record)
    return filepath


def main():
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} <zone_name>")
        sys.exit(1)

    zone_name = sys.argv[1]
    client = VinylDNSClient(VINYLDNS_HOST, VINYLDNS_ACCESS_KEY, VINYLDNS_SECRET_KEY)
    records = dump_zone_records(client, zone_name)

    print(json.dumps(records, indent=2))

    csv_file_path = write_records_to_csv(records, zone_name)
    print(f"CSV file written to: {csv_file_path}")


if __name__ == "__main__":
    main()
