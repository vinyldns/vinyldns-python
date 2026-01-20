import argparse
import logging
import os
import json
import sys
import ipaddress
from typing import List, Dict, Any
from datetime import datetime
from vinyldns.client import VinylDNSClient

"""
Converts IPv4/IPv6 subnets to reverse DNS zone names and verifies if zones exist in VinylDNS.

Environment variables must be set for VinylDNS authentication:
    - VINYLDNS_HOST
    - VINYLDNS_ACCESS_KEY
    - VINYLDNS_SECRET_KEY

Usage:
    python verify_reverse_zones.py <subnets_file>
    
Output:
    JSON format showing subnet, corresponding zone name, and existence status
    
Example input file content:
    192.168.1.0/24
    2001:558:4ffe:3::/64
    10.0.0.0/16
    
Example output:
    {
        "subnet": "192.168.1.0/24",
        "zone_name": "1.168.192.in-addr.arpa",
        "exists": true,
        "zone_id": "12345-abcd-6789"
    },
    {
        "subnet": "2001:558:4ffe:3::/64",
        "zone_name": "3.0.0.0.e.f.f.4.8.5.5.0.1.0.0.2.ip6.arpa",
        "exists": true,
        "zone_id": "12345-abcd-9876"
    }
"""

REQUIRED_ENV_VARS = ["VINYLDNS_HOST", "VINYLDNS_ACCESS_KEY", "VINYLDNS_SECRET_KEY"]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)


def safe_get_env_vars(env_vars: List[str]) -> Dict[str, str]:
    """
    Validate that all required environment variables exist and return their values.

    Args:
        env_vars (List[str]): List of environment variable names (strings) to check and retrieve.

    Returns:
        Dict[str, str]: Dictionary mapping environment variable names to their string values.

    Raises:
        EnvironmentError: If any of the required environment variables are missing.
    """
    missing = [v for v in env_vars if v not in os.environ]
    if missing:
        raise EnvironmentError(f"Missing env vars: {missing}")
    return {v: os.environ[v] for v in env_vars}


def ipv4_subnet_to_reverse_zone(subnet: str) -> str:
    """
    Convert an IPv4 subnet to its reverse DNS zone name.
    
    Args:
        subnet (str): IPv4 subnet in CIDR notation (e.g., "192.168.1.0/24")
    
    Returns:
        str: Reverse DNS zone name (e.g., "1.168.192.in-addr.arpa")
    """
    try:
        network = ipaddress.IPv4Network(subnet, strict=False)
        
        # Get the network address and prefix length
        network_addr = network.network_address
        prefix_length = network.prefixlen
        
        # Convert to octets
        octets = str(network_addr).split('.')
        
        # Calculate how many octets we need based on prefix length
        # Each octet represents 8 bits
        octets_needed = prefix_length // 8
        
        # Take the required octets from the beginning and reverse them
        relevant_octets = octets[:octets_needed]
        reversed_octets = '.'.join(reversed(relevant_octets))
        
        # Add the in-addr.arpa suffix
        reverse_zone = f"{reversed_octets}.in-addr.arpa"
        
        return reverse_zone
        
    except Exception as e:
        logging.error(f"Error converting IPv4 subnet {subnet} to reverse zone: {e}")
        return ""


def ipv6_subnet_to_reverse_zone(subnet: str) -> str:
    """
    Convert an IPv6 subnet to its reverse DNS zone name.
    
    Args:
        subnet (str): IPv6 subnet in CIDR notation (e.g., "2001:558:4ffe:3::/64")
    
    Returns:
        str: Reverse DNS zone name (e.g., "3.0.0.0.e.f.f.4.8.5.5.0.1.0.0.2.ip6.arpa")
    """
    try:
        network = ipaddress.IPv6Network(subnet, strict=False)
        
        # Get the network address and prefix length
        network_addr = network.network_address
        prefix_length = network.prefixlen
        
        # Convert to full hex representation (32 hex digits)
        full_hex = format(int(network_addr), '032x')
        
        # Calculate how many nibbles (4-bit hex digits) we need based on prefix length
        # Each nibble represents 4 bits
        nibbles_needed = prefix_length // 4
        
        # Take the required nibbles from the beginning
        relevant_hex = full_hex[:nibbles_needed]
        
        # Reverse the nibbles and add dots between them
        reversed_nibbles = '.'.join(reversed(relevant_hex))
        
        # Add the ip6.arpa suffix
        reverse_zone = f"{reversed_nibbles}.ip6.arpa"
        
        return reverse_zone
        
    except Exception as e:
        logging.error(f"Error converting IPv6 subnet {subnet} to reverse zone: {e}")
        return ""


def subnet_to_reverse_zone(subnet: str) -> str:
    """
    Convert an IPv4 or IPv6 subnet to its reverse DNS zone name.
    
    Args:
        subnet (str): IP subnet in CIDR notation (e.g., "192.168.1.0/24" or "2001:558:4ffe:3::/64")
    
    Returns:
        str: Reverse DNS zone name
    """
    try:
        # Try to determine if it's IPv4 or IPv6
        if ':' in subnet:
            return ipv6_subnet_to_reverse_zone(subnet)
        else:
            return ipv4_subnet_to_reverse_zone(subnet)
    except Exception as e:
        logging.error(f"Error determining IP version for subnet {subnet}: {e}")
        return ""


def read_ip_subnets(file_path: str) -> List[str]:
    """
    Read IPv4/IPv6 subnets from a text file.
    
    Args:
        file_path (str): Path to the file containing IP subnets
    
    Returns:
        List[str]: List of IP subnets (both IPv4 and IPv6)
    """
    subnets = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                # Skip empty lines and table formatting
                if not line or line.startswith('+') or line.startswith('|') or 'rows in set' in line:
                    continue
                
                # Skip header lines
                if line.startswith('name') or line == 'name':
                    continue
                    
                # Check if line contains a subnet (IPv4 or IPv6)
                if '/' in line:
                    # IPv6 subnet (contains ::)
                    if '::' in line or ':' in line:
                        subnets.append(line)
                    # IPv4 subnet (contains dots)
                    elif '.' in line:
                        subnets.append(line)
                    # Generic subnet with CIDR notation
                    else:
                        subnets.append(line)
        
        logging.info(f"Read {len(subnets)} IP subnets from {file_path}")
        return subnets
        
    except FileNotFoundError:
        logging.error(f"File not found: {file_path}")
        raise
    except Exception as e:
        logging.error(f"Error reading file {file_path}: {e}")
        raise


def check_zone_exists(client: VinylDNSClient, zone_name: str) -> Dict[str, Any]:
    """
    Check if a zone exists in VinylDNS.
    
    Args:
        client (VinylDNSClient): Initialized VinylDNS client instance
        zone_name (str): Name of the DNS zone to check
    
    Returns:
        Dict[str, Any]: Dictionary with zone information or error details
    """
    try:
        zone = client.get_zone_by_name(zone_name)
        if zone:
            return {
                "exists": True,
                "zone_id": zone.id,
                "zone_name": zone.name,
                "status": zone.status,
                "error": None
            }
        else:
            logging.warning(f"Zone not found log: {zone_name}")
            return {
                "exists": False,
                "zone_id": None,
                "zone_name": zone_name,
                "status": None,
                "error": "Zone not found"
            }
    except Exception as e:
        return {
            "exists": False,
            "zone_id": None,
            "zone_name": zone_name,
            "status": None,
            "error": str(e)
        }


def verify_ip_zones(client: VinylDNSClient, subnets: List[str]) -> List[Dict[str, Any]]:
    """
    Verify if reverse DNS zones exist for the given IP subnets (IPv4 and IPv6).
    
    Args:
        client (VinylDNSClient): Initialized VinylDNS client instance
        subnets (List[str]): List of IP subnets to check
    
    Returns:
        List[Dict[str, Any]]: List of dictionaries with verification results
    """
    results = []
    
    for i, subnet in enumerate(subnets, 1):
        logging.info(f"Processing subnet {i}/{len(subnets)}: {subnet}")
        
        # Convert subnet to reverse zone name
        reverse_zone = subnet_to_reverse_zone(subnet)
        
        if not reverse_zone:
            result = {
                "subnet": subnet,
                "zone_name": "",
                "exists": False,
                "zone_id": None,
                "status": None,
                "error": "Failed to convert subnet to reverse zone name"
            }
        else:
            # Check if zone exists
            zone_info = check_zone_exists(client, reverse_zone)
            result = {
                "subnet": subnet,
                "zone_name": reverse_zone,
                "exists": zone_info["exists"],
                "zone_id": zone_info["zone_id"],
                "status": zone_info["status"],
                "error": zone_info["error"]
            }
        
        results.append(result)
    
    return results


def write_results_to_file(results: List[Dict[str, Any]], output_dir: str = "output") -> str:
    """
    Write verification results to a timestamped JSON file.
    
    Args:
        results (List[Dict[str, Any]]): List of verification results
        output_dir (str, optional): Directory to save the file. Defaults to "output"
    
    Returns:
        str: Full file path of the written file
    """
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"ip_zone_verification_{timestamp}.json"
    filepath = os.path.join(output_dir, filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        
        logging.info(f"Results written to: {filepath}")
        return filepath
        
    except Exception as e:
        logging.error(f"Error writing results to {filepath}: {e}")
        raise


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert IPv4/IPv6 subnets to reverse DNS zones and verify their existence in VinylDNS"
    )
    parser.add_argument(
        "subnets_file",
        type=str,
        help="Path to file containing IP subnets (one per line, supports both IPv4 and IPv6)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="output",
        help="Directory to save output files (default: output)"
    )
    
    args = parser.parse_args()
    
    try:
        # Validate environment variables
        env_vars = safe_get_env_vars(REQUIRED_ENV_VARS)
        
        # Initialize VinylDNS client
        client = VinylDNSClient(
            env_vars["VINYLDNS_HOST"],
            env_vars["VINYLDNS_ACCESS_KEY"],
            env_vars["VINYLDNS_SECRET_KEY"],
        )
        
        # Read IP subnets from file
        subnets = read_ip_subnets(args.subnets_file)
        
        if not subnets:
            logging.error("No valid IP subnets found in the input file")
            sys.exit(2)
        
        # Verify zones
        results = verify_ip_zones(client, subnets)
        
        # Output results to stdout
        print(json.dumps(results, indent=2))
        
        # Write results to file
        write_results_to_file(results, args.output_dir)
        
        # Print summary
        total = len(results)
        existing = sum(1 for r in results if r["exists"])
        missing = total - existing
        
        logging.info(f"Summary: {existing}/{total} zones exist, {missing} zones missing")
        
    except EnvironmentError as env_err:
        logging.error(f"Environment error: {env_err}")
        sys.exit(3)
    except Exception as e:
        logging.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(4)


if __name__ == "__main__":
    main()