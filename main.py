import requests
import configparser
import sys
from typing import List

# GitHub API base URL
GITHUB_API_URL = "https://api.github.com"

# Define network-related Terraform strings to search for
NETWORK_TERMS = [
    "aws_vpc", "aws_subnet", "aws_subnet_association", "aws_route_table", "aws_route_table_association",
    "aws_default_route_table", "aws_internet_gateway", "aws_nat_gateway", "aws_eip", "aws_security_group",
    "aws_security_group_rule", "aws_network_acl", "aws_network_acl_rule", "aws_lb", "aws_alb", "aws_lb_listener",
    "aws_lb_target_group", "aws_lb_target_group_attachment", "aws_dx_gateway", "aws_dx_connection",
    "aws_vpn_gateway", "aws_customer_gateway", "aws_vpn_connection", "aws_transit_gateway",
    "aws_transit_gateway_vpc_attachment", "aws_transit_gateway_route", "aws_transit_gateway_route_table",
    "aws_vpc_endpoint", "aws_vpc_endpoint_service", "cidr_block", "ingress", "egress", "destination_cidr_block",
    "source_security_group_id", "availability_zone", "private", "public", "enable_dns_hostnames",
    "enable_dns_support"
]

def load_config(config_file: str):
    """Loads configuration settings from a file."""
    config = configparser.ConfigParser()
    config.read(config_file)
    return config

def get_github_headers(token: str):
    """Returns headers for GitHub API authentication."""
    return {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}

def get_pull_requests(repo: str, token: str) -> List[dict]:
    """Fetches all pull requests for the given repository."""
    url = f"{GITHUB_API_URL}/repos/{repo}/pulls"
    headers = get_github_headers(token)
    params = {"state": "all", "per_page": 100}
    pr_list = []

    while url:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            print(f"Failed to fetch PRs: {response.status_code} {response.text}")
            sys.exit(1)
        pr_list.extend(response.json())
        url = response.links.get("next", {}).get("url")  # Handle pagination

    return pr_list

def get_pr_files(repo: str, pr_number: int, token: str) -> List[dict]:
    """Fetches the list of changed files in a PR."""
    url = f"{GITHUB_API_URL}/repos/{repo}/pulls/{pr_number}/files"
    headers = get_github_headers(token)
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"Failed to fetch PR files: {response.status_code} {response.text}")
        return []

    return response.json()

def get_file_patch(file_data: dict) -> str:
    """Extracts the changed code (patch) from a file in a PR."""
    return file_data.get("patch", "")

def search_for_network_changes(patch: str) -> bool:
    """Checks if the changed code contains network-related Terraform terms."""
    return any(term in patch for term in NETWORK_TERMS)

def analyze_pull_requests(repo: str, token: str):
    """Analyzes PRs for Terraform network-related changes."""
    pull_requests = get_pull_requests(repo, token)

    for pr in pull_requests:
        pr_number = pr["number"]
        print(f"Analyzing PR #{pr_number} - {pr['title']}")

        pr_files = get_pr_files(repo, pr_number, token)
        for file in pr_files:
            if file["filename"].endswith(".tf"):  # Only check Terraform files
                patch = get_file_patch(file)
                if search_for_network_changes(patch):
                    print(f"  🔥 Network-related Terraform change detected in: {file['filename']} (PR #{pr_number})")

def main():
    """Main function to execute the script."""
    config = load_config("config.ini")

    try:
        token = config["github"]["token"]
        repo = config["github"]["repo"]
    except KeyError as e:
        print(f"Missing configuration key: {e}")
        sys.exit(1)

    analyze_pull_requests(repo, token)

if __name__ == "__main__":
    main()
