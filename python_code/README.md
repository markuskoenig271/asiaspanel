# Azure access test (python)

This small test script helps validate you can authenticate and access:
- an Azure Subscription / Resource Group (via `azure-mgmt-resource`)
- Blob Storage (via `azure-storage-blob`)

Prerequisites
- Python 3.8+
- `az` CLI or environment credentials (the script uses `DefaultAzureCredential`):
  - `az login` (for interactive), or
  - set `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_CLIENT_SECRET` for service principal, or
  - run from an Azure VM/Function with managed identity.

Install

PowerShell (from repo root):
```powershell
python -m pip install -r .\python_code\requirements.txt
```

Quick test

Show help / validate script runs:
```powershell
python .\python_code\test_azure_access.py --help
```

Example usage (requires an actual subscription id and storage account name):
```powershell
# List resource groups in a subscription
python .\python_code\test_azure_access.py --subscription <SUB_ID> --list-rgs

# Check a single resource group and list containers in a storage account
python .\python_code\test_azure_access.py --subscription <SUB_ID> --resource-group <RG> --storage-account <STORAGE_ACCOUNT>

# List blobs in a container
python .\python_code\test_azure_access.py --storage-account <STORAGE_ACCOUNT> --container <CONTAINER>
```

Notes
- If you get authentication errors, ensure `az login` is done in the same account as VS Code or export the service principal environment variables.
- For storage access via `DefaultAzureCredential`, the Storage account must accept AAD token auth (it usually does). If you prefer key-based auth, use the connection string and `BlobServiceClient.from_connection_string()`.

Quick run (Anaconda Prompt / VS Code terminal)

1) Open the Anaconda Prompt terminal in VS Code (Terminal → New Terminal → Anaconda Prompt) or open your Anaconda Prompt.

2) Activate the conda environment:

```powershell
conda activate asia_01
```

3) Verify Python and install deps (if not already):

```powershell
python --version
pip install -r .\python_code\requirements.txt
```

4) Verify Azure CLI is available and sign in:

```powershell
az --version
az login --use-device-code
# optionally set the subscription to use
az account set --subscription <SUBSCRIPTION_ID_OR_NAME>
az account show -o table
```

5) Run the test script (examples):

```powershell
# show help
python .\python_code\test_azure_access.py --help

# list resource groups in a subscription
python .\python_code\test_azure_access.py --subscription <SUB_ID> --list-rgs

# check a resource group and list containers in a storage account
python .\python_code\test_azure_access.py --subscription <SUB_ID>  --resource-group rg-asiaspanel-dev --storage-account stasiaspaneldev

# list blobs in a container
python .\python_code\test_azure_access.py --storage-account stasiaspaneldev --container <CONTAINER>
```

If you prefer not to activate the environment, you can run the script with `conda run`:

```powershell
& "C:\\Users\\marku\\Miniconda3\\Scripts\\conda.exe" run -n asia_01 --no-capture-output python .\python_code\test_azure_access.py --list-rgs
```


az resource show --ids "/subscriptions/<subscr>/resourceGroups/rg-asiaspanel-dev/providers/Microsoft.Web/staticSites/asiaspanel-web" -o json
