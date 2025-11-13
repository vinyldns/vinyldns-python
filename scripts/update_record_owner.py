import argparse
import csv
import logging
import os
import sys
from vinyldns.client import VinylDNSClient

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


def read_record_names_from_csv(csv_path: str) -> list[str]:
    """
    Reads a CSV file containing DNS records and extracts unique FQDNs.

    Args:
        csv_path (str): Path to the CSV file.

    Returns:
        list[str]: List of unique FQDN record names found in the CSV.
    """
    record_names = set()
    try:
        with open(csv_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            if 'fqdn' not in reader.fieldnames:
                raise ValueError("CSV missing required 'fqdn' column")
            for row in reader:
                fqdn = row.get('fqdn')
                if fqdn:
                    record_names.add(fqdn)
        return list(record_names)
    except Exception as e:
        logging.error(f"Failed to read CSV file {csv_path}: {e}")
        raise


def update_record_owner_group(client: VinylDNSClient, record_names: list[str], old_owner_group_id: str,
                              new_owner_group_id: str) -> None:
    """
    Updates the owner group of all record sets matching provided record names.

    Args:
        client (VinylDNSClient): An authenticated VinylDNS client instance.
        record_names (list[str]): List of fully qualified domain names to update.
        old_owner_group_id (str): The old owner group ID to update.
        new_owner_group_id (str): The new owner group ID to apply.
    """
    for record_name in record_names:
        try:
            response = client.search_record_sets(record_name_filter=record_name,
                                                 record_owner_group_filter=old_owner_group_id)
            for recordset in response.record_sets:
                if recordset.owner_group_id != new_owner_group_id:
                    logging.info(
                        f"Updating owner group for {recordset.fqdn} from {recordset.owner_group_id} "
                        f"to {new_owner_group_id}")
                    recordset.owner_group_id = new_owner_group_id
                    updated = client.update_record_set(recordset)
                    logging.info(f"Updated owner group: {updated.record_set.owner_group_id}")
                else:
                    logging.info(
                        f"Record {recordset.fqdn} is already owned by group {new_owner_group_id}; skipping")
        except Exception as e:
            logging.error(f"Failed to update record {record_name}: {e}")


def main() -> None:
    """
    Reads a list of DNS records from a CSV file, and updates their ownership in VinylDNS
    using the provided owner group ID.

    Environment variables must be set for VinylDNS authentication:
        - VINYLDNS_HOST
        - VINYLDNS_ACCESS_KEY
        - VINYLDNS_SECRET_KEY

    Usage:
        python update_record_owner_group.py <path_to_records_csv> <old_owner_group_id> <new_owner_group_id>
    """
    parser = argparse.ArgumentParser(
        description="Update Vinyldns ownership for all records in a list of records.")
    parser.add_argument(
        "csv_file",
        type=str,
        help="Path to CSV file containing DNS records (must include 'fqdn' column)."
    )
    parser.add_argument(
        "old_owner_group_id",
        type=str,
        help="Old owner group ID to update."
    )
    parser.add_argument(
        "new_owner_group_id",
        type=str,
        help="New owner group ID to assign to these records."
    )
    args = parser.parse_args()

    try:
        env_vars = safe_get_env_vars(REQUIRED_ENV_VARS)
        client = VinylDNSClient(
            env_vars["VINYLDNS_HOST"],
            env_vars["VINYLDNS_ACCESS_KEY"],
            env_vars["VINYLDNS_SECRET_KEY"],
        )

        record_names = read_record_names_from_csv(args.csv_file)
        logging.info(f"Loaded {len(record_names)} unique DNS records from CSV {args.csv_file}")

        update_record_owner_group(client, record_names, args.old_owner_group_id, args.new_owner_group_id)

    except EnvironmentError as env_err:
        logging.error(f"Environment error: {env_err}")
        sys.exit(3)
    except Exception as e:
        logging.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(4)


if __name__ == "__main__":
    main()
