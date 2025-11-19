import argparse
import csv
import logging
import os
import json
import sys
from typing import Any
from datetime import datetime
from vinyldns.client import VinylDNSClient

"""
Fetches all DNS records from the matching zone.
Outputs result in JSON format to stdout and writes to a timestamped CSV file.

Environment variables must be set for VinylDNS authentication:
    - VINYLDNS_HOST
    - VINYLDNS_ACCESS_KEY
    - VINYLDNS_SECRET_KEY

Usage:
    python zone_dump.py <zone_name>
    
Output example:
    fqdn,type,record_data
    test.example.com.,A,1.2.3.4
    testcname.example.com.,CNAME,test.example.com.
"""

REQUIRED_ENV_VARS = ["VINYLDNS_HOST", "VINYLDNS_ACCESS_KEY", "VINYLDNS_SECRET_KEY"]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)


def safe_get_env_vars(env_vars: list[str]) -> dict[str, str]:
    """
    Validate that all required environment variables exist and return their values.

    Args:
        env_vars (list[str]): List of environment variable names (strings) to check and retrieve.

    Returns:
        dict[str, str]: Dictionary mapping environment variable names to their string values.

    Raises:
        EnvironmentError: If any of the required environment variables are missing.
    """
    missing = [v for v in env_vars if v not in os.environ]
    if missing:
        raise EnvironmentError(f"Missing env vars: {missing}")
    return {v: os.environ[v] for v in env_vars}


def format_record_data(record_type: str, record: Any) -> str:
    """
    Format DNS record data into a human-readable string based on its type.

    Args:
        record_type (str): The DNS record type (e.g., 'A', 'MX', 'TXT').
        record (Any): The record object containing fields relevant to the type.

    Returns:
        str: A formatted string describing the record contents.
             Returns an informative message if the record type is unsupported.
    """
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
        "SSHFP": lambda r: (
            f"algorithm: {r.algorithm}, type: {r.type}, fingerprint: {r.fingerprint}"
        )
    }
    if record_type not in formatters:
        logging.warning(f"Could not retrieve record data for unsupported record type: {record_type}")
        return f"could not retrieve record data for record type: {record_type}"

    return formatters[record_type](record)


def dump_zone_records(client: VinylDNSClient, zone_name: str) -> list[dict[str, str]]:
    """
    Dump DNS records of a specified zone.

    Args:
        client (VinylDNSClient): Initialized VinylDNS client instance.
        zone_name (str): Name of the DNS zone.

    Returns:
        list[dict[str, str]]: List of dictionaries with keys 'fqdn', 'type', and formatted 'record_data'.
    """
    zone = client.get_zone_by_name(zone_name)
    if zone is None:
        logging.error(f"Zone with name {zone_name} does not exist. Please check your zone name.")
    all_records = []
    next_id = None

    while zone:
        response = client.list_record_sets(zone.id, start_from=next_id)
        for record_set in response.record_sets:
            record_type = record_set.type
            for record in record_set.records:
                record_info = {
                    "fqdn": record_set.fqdn,
                    "type": record_set.type,
                    "record_data": format_record_data(record_type, record)
                }
                all_records.append(record_info)
        next_id = response.next_id
        if not next_id:
            break

    return all_records


def write_records_to_csv(records: list[dict[str, str]], zone_name: str, output_dir: str = "output") -> str:
    """
    Write a list of DNS record dictionaries to a timestamped CSV file.

    Args:
        records (list[dict[str, str]]): List of record dictionaries to write to CSV.
        zone_name (str): Zone name used to name the CSV file safely.
        output_dir (str, optional): Directory to save the CSV file. Defaults to "output".

    Returns:
        str: Full file path of the written CSV file.

    Raises:
        OSError: If there is an error creating the directory or writing the CSV file,
                 such as permission errors or disk IO problems.
    """
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_zone_name = zone_name.rstrip('.').replace('.', '_')
    filename = f"{safe_zone_name}_records_{timestamp}.csv"
    filepath = os.path.join(output_dir, filename)

    fieldnames = ["fqdn", "type", "record_data"]
    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for record in records:
                writer.writerow(record)
        logging.info(f"CSV file successfully written: {filepath}")
    except OSError as e:
        logging.error(f"Failed to write CSV file {filepath}: {e}")
        raise

    return filepath


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Dump VinylDNS zone records and output results."
    )
    parser.add_argument(
        "zone_name",
        type=str,
        help="Zone name to dump records from"
    )

    args = parser.parse_args()

    try:
        env_vars = safe_get_env_vars(REQUIRED_ENV_VARS)
        client = VinylDNSClient(
            env_vars["VINYLDNS_HOST"],
            env_vars["VINYLDNS_ACCESS_KEY"],
            env_vars["VINYLDNS_SECRET_KEY"],
        )

        records = dump_zone_records(client, args.zone_name)

        print(json.dumps(records, indent=2))

        write_records_to_csv(records, args.zone_name)

    except EnvironmentError as env_err:
        logging.error(f"Environment error: {env_err}")
        sys.exit(3)
    except Exception as e:
        logging.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(4)


if __name__ == "__main__":
    main()
