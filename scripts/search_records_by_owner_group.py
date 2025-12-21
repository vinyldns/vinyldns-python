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
Loads record name filters from the specified file and fetches matching DNS records
from VinylDNS filtered by owner group and record names. The record name filter file specifies what domains to search in.
Outputs result in JSON format to stdout and writes to a timestamped CSV file.

Environment variables must be set for VinylDNS authentication:
    - VINYLDNS_HOST
    - VINYLDNS_ACCESS_KEY
    - VINYLDNS_SECRET_KEY

Usage:
    python search_records_by_owner_group.py <path_to_filter_file> <owner_group_id>
    
Record Name Filter File Example:
    *.arpa.
    *.com.
    *.net.
    ...
    
Output Example:
    fqdn,type,record_data
    test.example.com.,A,1.2.3.4
    4.3.2.1.in-addr.arpa.,PTR,test.example.com.
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


def load_filters_from_file(filepath: str) -> list[str]:
    """
    Load record name filters from a specified file.

    Reads the file line by line and returns a list of filter strings.
    Lines that are empty or start with '#' (treated as comments) are ignored.

    Args:
        filepath (str): Path to the filter file containing one record name filter per line.

    Returns:
        list[str]: A list of record name filter strings extracted from the file.

    Raises:
        OSError: If the file cannot be opened or read due to operating system-related errors,
                 including file not found, permissions, or other I/O issues.
        Exception: For any other unexpected errors encountered while reading the file.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith("#")]
    except Exception as e:
        logging.error(f"Error loading filter file '{filepath}': {e}")
        raise


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


def search_records_by_owner_group(client: VinylDNSClient, record_owner_filter: str,
                                  record_name_filter_list: list[str]) -> list[dict[str, str]]:
    """
    Search VinylDNS records filtered by owner group and multiple record name filters.

    Iterates over each record name filter pattern and fetches matching DNS records
    from VinylDNS restricted by the owner group filter. Aggregates all matching
    records into a single result list.

    Args:
        client (VinylDNSClient): Initialized VinylDNS client instance used for API calls.
        record_owner_filter (str): Owner group filter string to restrict record search.
        record_name_filter_list (list[str]): List of record name filter patterns (wildcards allowed).

    Returns:
        list[dict[str, str]]: A list of dictionaries, each with keys:
            - 'fqdn': Fully qualified domain name of the record set.
            - 'type': DNS record type as a string.
            - 'record_data': Formatted string describing the DNS record's data.
    """
    all_records = []
    group = client.get_group(record_owner_filter)
    if group is None:
        logging.error(f"Group with ID {record_owner_filter} not found. Please check your group ID.")
        return all_records

    for name_filter in record_name_filter_list:
        next_id = None
        while True:
            response = client.search_record_sets(
                start_from=next_id,
                record_name_filter=name_filter,
                record_owner_group_filter=record_owner_filter
            )
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
    if not all_records:
        logging.error(f"No records found matching owner group {record_owner_filter}.")

    return all_records


def write_records_to_csv(records: list[dict[str, str]], owner_group_id: str, output_dir: str = "output") -> str:
    """
    Write a list of DNS record dictionaries to a timestamped CSV file.

    Args:
        records (list[dict[str, str]]): List of record dictionaries to write to CSV.
        owner_group_id (str): Owner group ID used to name the CSV file safely.
        output_dir (str, optional): Directory to save the CSV file. Defaults to "output".

    Returns:
        str: Full file path of the written CSV file.

    Raises:
        OSError: If there is an error creating the directory or writing the CSV file,
                 such as permission errors or disk IO problems.
    """
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{owner_group_id}_records_by_owner_group_{timestamp}.csv"
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
        description="Search VinylDNS records filtered by owner group and record name patterns."
    )
    parser.add_argument(
        "filter_file",
        type=str,
        help="Path to a file containing record name filters, one per line."
    )
    parser.add_argument(
        "owner_group_id",
        type=str,
        help="Owner group ID filter for DNS record search"
    )
    args = parser.parse_args()

    try:
        record_name_filter_list = load_filters_from_file(args.filter_file)
        env_vars = safe_get_env_vars(REQUIRED_ENV_VARS)
        client = VinylDNSClient(
            env_vars["VINYLDNS_HOST"],
            env_vars["VINYLDNS_ACCESS_KEY"],
            env_vars["VINYLDNS_SECRET_KEY"],
        )

        records = search_records_by_owner_group(client, args.owner_group_id, record_name_filter_list)

        print(json.dumps(records, indent=2))

        write_records_to_csv(records, args.owner_group_id)

    except EnvironmentError as env_err:
        logging.error(f"Environment error: {env_err}")
        sys.exit(3)
    except Exception as e:
        logging.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(4)


if __name__ == "__main__":
    main()
