import argparse
import subprocess
import sys
from pathlib import Path

def run(cmd):
    print(f"\n$ {' '.join(cmd)}")
    subprocess.check_call(cmd)

if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser(description="Destroy Terraform stacks for Azure OpenAI and Databricks.")
        group = parser.add_mutually_exclusive_group()
        group.add_argument("--rg-only", action="store_true", help="Destroy only the resource group stack")
        group.add_argument("--openai-only", action="store_true", help="Destroy only the Azure OpenAI account stack")
        group.add_argument("--deployment-only", action="store_true", help="Destroy only the Azure OpenAI deployment stack")
        group.add_argument("--databricks-only", action="store_true", help="Destroy only the Databricks workspace stack")
        group.add_argument("--keyvault-only", action="store_true", help="Destroy only the Key Vault stack")
        group.add_argument("--compute-only", action="store_true", help="Destroy only the Databricks compute stack")
        group.add_argument("--notebooks-only", action="store_true", help="Destroy only the notebooks stack")
        group.add_argument("--serving-only", action="store_true", help="Destroy only the serving endpoint stack")
        args = parser.parse_args()

        repo_root = Path(__file__).resolve().parent.parent
        rg_dir = repo_root / "terraform" / "01_resource_group"
        openai_dir = repo_root / "terraform" / "02_azure_openai"
        deployment_dir = repo_root / "terraform" / "03_openai_deployment"
        databricks_dir = repo_root / "terraform" / "04_databricks_workspace"
        key_vault_dir = repo_root / "terraform" / "05_key_vault"
        compute_dir = repo_root / "terraform" / "06_databricks_compute"
        notebooks_dir = repo_root / "terraform" / "07_notebooks"
        serving_dir = repo_root / "terraform" / "08_serving_endpoint"

        if args.rg_only:
            tf_dirs = [rg_dir]
        elif args.openai_only:
            tf_dirs = [openai_dir]
        elif args.deployment_only:
            tf_dirs = [deployment_dir]
        elif args.databricks_only:
            tf_dirs = [databricks_dir]
        elif args.keyvault_only:
            tf_dirs = [key_vault_dir]
        elif args.compute_only:
            tf_dirs = [compute_dir]
        elif args.notebooks_only:
            tf_dirs = [notebooks_dir]
        elif args.serving_only:
            tf_dirs = [serving_dir]
        else:
            tf_dirs = [serving_dir, notebooks_dir, compute_dir, key_vault_dir, databricks_dir, deployment_dir, openai_dir, rg_dir]

        for tf_dir in tf_dirs:
            if not tf_dir.exists():
                raise FileNotFoundError(f"Missing Terraform dir: {tf_dir}")
            run(["terraform", f"-chdir={tf_dir}", "destroy", "-auto-approve"])
    except subprocess.CalledProcessError as exc:
        print(f"Command failed: {exc}")
        sys.exit(exc.returncode)
