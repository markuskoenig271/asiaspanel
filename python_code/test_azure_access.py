#!/usr/bin/env python3
"""
Small test program to validate Azure subscription, resource group and Blob Storage access.

Usage examples (PowerShell):
  # interactive with az login credentials
  az login
  python .\python_code\test_azure_access.py --subscription <SUB_ID> --resource-group <RG> --storage-account <STORAGE_ACCOUNT> --container <CONTAINER>

The script uses DefaultAzureCredential (works with `az login`, environment variables, managed identity, etc.).
See README.md for details.
"""
import argparse
import logging
import sys
from typing import Optional

from azure.identity import DefaultAzureCredential
from azure.core.exceptions import HttpResponseError
from azure.mgmt.resource import ResourceManagementClient
from azure.storage.blob import BlobServiceClient


def list_resource_groups(subscription_id: str, cred: DefaultAzureCredential):
    print(f"Connecting to Resource Management for subscription: {subscription_id}")
    client = ResourceManagementClient(cred, subscription_id)
    try:
        rgs = list(client.resource_groups.list())
        print(f"Found {len(rgs)} resource groups (showing up to 20):")
        for rg in rgs[:20]:
            print(f" - {rg.name}")
    except HttpResponseError as e:
        print("Failed to list resource groups:", e)


def check_resource_group(subscription_id: str, resource_group: str, cred: DefaultAzureCredential):
    client = ResourceManagementClient(cred, subscription_id)
    try:
        rg = client.resource_groups.get(resource_group)
        print(f"Resource group '{resource_group}' exists. Location: {rg.location}")
    except HttpResponseError as e:
        print(f"Could not get resource group '{resource_group}': {e}")


def list_blobs(storage_account: str, container: Optional[str], cred: DefaultAzureCredential):
    account_url = f"https://{storage_account}.blob.core.windows.net"
    print(f"Connecting to storage account at {account_url}")
    try:
        svc = BlobServiceClient(account_url=account_url, credential=cred)
        if container:
            container_client = svc.get_container_client(container)
            print(f"Listing blobs in container '{container}':")
            for i, blob in enumerate(container_client.list_blobs()):
                print(f" - {blob.name}")
                if i >= 100:
                    print(" (truncated after 100 blobs)")
                    break
        else:
            print("Listing containers:")
            for c in svc.list_containers():
                print(f" - {c['name']}")
    except Exception as e:
        print("Failed to access blob storage:", e)


def main(argv):
    parser = argparse.ArgumentParser(description="Test Azure subscription, resource group and Blob Storage access using DefaultAzureCredential.")
    parser.add_argument("--subscription", help="Subscription ID to use (required for resource group checks)")
    parser.add_argument("--resource-group", help="Resource group name to check")
    parser.add_argument("--storage-account", help="Storage account name (without .blob.core.windows.net)")
    parser.add_argument("--container", help="Container name to list blobs from (optional)")
    parser.add_argument("--list-rgs", action="store_true", help="List resource groups in the subscription (shows up to 20)")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")

    args = parser.parse_args(argv)

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    cred = DefaultAzureCredential()

    if args.subscription:
        if args.list_rgs:
            list_resource_groups(args.subscription, cred)
        if args.resource_group:
            check_resource_group(args.subscription, args.resource_group, cred)
    else:
        print("No subscription provided; resource group checks skipped. You can provide --subscription <SUB_ID>.")

    if args.storage_account:
        list_blobs(args.storage_account, args.container, cred)
    else:
        print("No storage account provided; blob checks skipped. You can provide --storage-account <NAME>.")


if __name__ == "__main__":
    main(sys.argv[1:])
