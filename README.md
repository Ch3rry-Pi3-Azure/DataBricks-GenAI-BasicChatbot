# Azure OpenAI + Databricks Generative AI

Terraform-driven setup for a resource group, Azure OpenAI account + deployment, Azure Key Vault, and Azure Databricks workspace + compute.

## Quick Start
1) Install prerequisites:
   - Azure CLI (az)
   - Terraform (>= 1.5)
   - Python 3.10+

2) Authenticate to Azure:
```powershell
az login
az account show
```

3) Deploy infrastructure:
```powershell
python scripts\deploy.py
```

4) Open the notebook in Databricks and run the registration cell:
- `notebooks/BasicChatBot.ipynb` (registers model as `basic-chatbot`)

5) Deploy the serving endpoint:
```powershell
python scripts\deploy.py --serving-only
```

6) Query the endpoint (example payload):
```json
{
  "dataframe_split": {
    "columns": ["user_query"],
    "data": [["hello how are you?"]]
  }
}
```

## Project Structure
- terraform/01_resource_group: Azure resource group
- terraform/02_azure_openai: Azure OpenAI account
- terraform/03_openai_deployment: Azure OpenAI model deployment
- terraform/04_databricks_workspace: Azure Databricks workspace
- terraform/05_key_vault: Azure Key Vault for secrets
- terraform/06_databricks_compute: Databricks cluster + Key Vault-backed secret scope
- terraform/07_notebooks: Databricks workspace notebooks
- terraform/08_serving_endpoint: Databricks model serving endpoint
- scripts/: Deploy/destroy helpers (auto-writes terraform.tfvars and .env)
- guides/setup.md: Detailed setup guide
- notebooks/: Databricks notebooks (tracked)

## Deploy/Destroy Options
Deploy specific stacks:
```powershell
python scripts\deploy.py --rg-only
python scripts\deploy.py --openai-only
python scripts\deploy.py --deployment-only
python scripts\deploy.py --databricks-only
python scripts\deploy.py --keyvault-only
python scripts\deploy.py --compute-only
python scripts\deploy.py --notebooks-only
python scripts\deploy.py --serving-only
```

Destroy:
```powershell
python scripts\destroy.py
```

## Guide
See guides/setup.md for detailed instructions.
