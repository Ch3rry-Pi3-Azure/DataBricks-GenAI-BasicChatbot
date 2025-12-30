import argparse
import json
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

DEFAULTS = {
    "resource_group_name_prefix": "rg-dbgenai",
    "location": "eastus2",
    "account_name_prefix": "aoaidbgenai",
    "sku_name": "S0",
    "deployment_name": "gpt-5-chat",
    "model_name": "gpt-5-chat",
    "model_version": "2025-10-03",
    "scale_type": "GlobalStandard",
    "deployment_capacity": 1,
    "openai_api_version": "2024-02-15-preview",
    "workspace_name_prefix": "adb-genai",
    "databricks_sku": "premium",
    "key_vault_name_prefix": "kvdbgenai",
    "key_vault_sku_name": "standard",
    "secret_scope_name": "aoai-scope",
    "openai_pypi_package": "openai==1.56.0",
    "use_ml_runtime": True,
    "serving_endpoint_name": "basic-chatbot-endpoint",
    "serving_model_name": "basic-chatbot",
    "serving_model_version": None,
    "serving_workload_size": "Small",
    "serving_scale_to_zero": True,
    "serving_traffic_percentage": 100,
}

ENV_KEYS = [
    "OPENAI_API_BASE",
    "OPENAI_API_KEY",
    "OPENAI_API_VERSION",
    "OPENAI_DEPLOYMENT_NAME",
    "DATABRICKS_WORKSPACE_URL",
]

DATABRICKS_SP_APP_ID = "2ff814a6-3304-4ab8-85cb-cd0e6f879c1d"
KEY_VAULT_SECRET_NAMES = {
    "OPENAI_API_BASE": "openai-api-base",
    "OPENAI_API_KEY": "openai-api-key",
    "OPENAI_API_VERSION": "openai-api-version",
    "OPENAI_DEPLOYMENT_NAME": "openai-deployment-name",
}
AZ_FALLBACK_PATHS = [
    r"C:\Program Files (x86)\Microsoft SDKs\Azure\CLI2\wbin\az.cmd",
    r"C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd",
]

def find_az():
    az_path = shutil.which("az")
    if az_path:
        return az_path
    for path in AZ_FALLBACK_PATHS:
        if Path(path).exists():
            return path
    return None

AZ_BIN = find_az()

def run(cmd):
    print(f"\n$ {' '.join(cmd)}")
    subprocess.check_call(cmd)

def run_capture(cmd):
    print(f"\n$ {' '.join(cmd)}")
    return subprocess.check_output(cmd, text=True).strip()

def run_sensitive(cmd, redacted_indices):
    display_cmd = cmd[:]
    for index in redacted_indices:
        if 0 <= index < len(display_cmd):
            display_cmd[index] = "***"
    print(f"\n$ {' '.join(display_cmd)}")
    subprocess.check_call(cmd)

def run_apply_with_import(tf_dir, deployment_id):
    cmd = ["terraform", f"-chdir={tf_dir}", "apply", "-auto-approve"]
    print(f"\n$ {' '.join(cmd)}")
    result = subprocess.run(cmd, text=True, capture_output=True)
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    if result.returncode == 0:
        return
    combined = (result.stdout or "") + (result.stderr or "")
    if "already exists" in combined and "azurerm_cognitive_deployment" in combined:
        run(["terraform", f"-chdir={tf_dir}", "import", "azurerm_cognitive_deployment.main", deployment_id])
        run(cmd)
        return
    raise subprocess.CalledProcessError(result.returncode, cmd)

def hcl_value(value):
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    escaped = str(value).replace('"', '\\"')
    return f'"{escaped}"'

def write_tfvars(path, items):
    lines = [f"{key} = {hcl_value(value)}" for key, value in items]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

def get_output(tf_dir, output_name):
    return run_capture(["terraform", f"-chdir={tf_dir}", "output", "-raw", output_name])

def get_output_optional(tf_dir, output_name):
    try:
        return get_output(tf_dir, output_name)
    except subprocess.CalledProcessError:
        return None

def get_output_with_apply(tf_dir, output_name):
    try:
        return get_output(tf_dir, output_name)
    except subprocess.CalledProcessError:
        run(["terraform", f"-chdir={tf_dir}", "apply", "-auto-approve"])
        return get_output(tf_dir, output_name)

def write_rg_tfvars(rg_dir):
    items = [
        ("resource_group_name", None),
        ("resource_group_name_prefix", DEFAULTS["resource_group_name_prefix"]),
        ("location", DEFAULTS["location"]),
    ]
    write_tfvars(rg_dir / "terraform.tfvars", items)

def write_openai_tfvars(openai_dir, rg_name):
    items = [
        ("resource_group_name", rg_name),
        ("location", DEFAULTS["location"]),
        ("account_name_prefix", DEFAULTS["account_name_prefix"]),
        ("sku_name", DEFAULTS["sku_name"]),
    ]
    write_tfvars(openai_dir / "terraform.tfvars", items)

def write_deployment_tfvars(deployment_dir, rg_name, account_name):
    items = [
        ("resource_group_name", rg_name),
        ("account_name", account_name),
        ("deployment_name", DEFAULTS["deployment_name"]),
        ("model_name", DEFAULTS["model_name"]),
        ("model_version", DEFAULTS["model_version"]),
        ("scale_type", DEFAULTS["scale_type"]),
        ("deployment_capacity", DEFAULTS["deployment_capacity"]),
    ]
    write_tfvars(deployment_dir / "terraform.tfvars", items)

def write_key_vault_tfvars(kv_dir, rg_name):
    items = [
        ("resource_group_name", rg_name),
        ("location", DEFAULTS["location"]),
        ("key_vault_name_prefix", DEFAULTS["key_vault_name_prefix"]),
        ("sku_name", DEFAULTS["key_vault_sku_name"]),
    ]
    write_tfvars(kv_dir / "terraform.tfvars", items)

def write_databricks_tfvars(databricks_dir, rg_name):
    items = [
        ("resource_group_name", rg_name),
        ("location", DEFAULTS["location"]),
        ("workspace_name_prefix", DEFAULTS["workspace_name_prefix"]),
        ("sku", DEFAULTS["databricks_sku"]),
        ("managed_resource_group_name", None),
    ]
    write_tfvars(databricks_dir / "terraform.tfvars", items)

def write_databricks_compute_tfvars(compute_dir, rg_name):
    items = [
        ("resource_group_name", rg_name),
        ("secret_scope_name", DEFAULTS["secret_scope_name"]),
        ("openai_pypi_package", DEFAULTS["openai_pypi_package"]),
        ("use_ml_runtime", DEFAULTS["use_ml_runtime"]),
    ]
    write_tfvars(compute_dir / "terraform.tfvars", items)

def write_notebooks_tfvars(notebooks_dir, rg_name):
    items = [
        ("resource_group_name", rg_name),
    ]
    write_tfvars(notebooks_dir / "terraform.tfvars", items)

def write_serving_tfvars(serving_dir, rg_name, databricks_dir):
    if AZ_BIN is None:
        raise FileNotFoundError("Azure CLI not found. Install Azure CLI or ensure az is on PATH.")
    run(["terraform", f"-chdir={databricks_dir}", "init"])
    workspace_url = get_output(databricks_dir, "databricks_workspace_url")
    model_version = DEFAULTS["serving_model_version"]
    if model_version is None:
        token = get_databricks_aad_token()
        model_version = get_latest_model_version(workspace_url, token, DEFAULTS["serving_model_name"])
        if model_version is None:
            raise RuntimeError(
                f"Could not find any model versions for '{DEFAULTS['serving_model_name']}'. "
                "Register the model in MLflow before deploying the serving endpoint."
            )
    items = [
        ("resource_group_name", rg_name),
        ("endpoint_name", DEFAULTS["serving_endpoint_name"]),
        ("served_model_name", DEFAULTS["serving_model_name"]),
        ("model_name", DEFAULTS["serving_model_name"]),
        ("model_version", model_version),
        ("secret_scope_name", DEFAULTS["secret_scope_name"]),
        ("workload_size", DEFAULTS["serving_workload_size"]),
        ("scale_to_zero_enabled", DEFAULTS["serving_scale_to_zero"]),
        ("traffic_percentage", DEFAULTS["serving_traffic_percentage"]),
    ]
    write_tfvars(serving_dir / "terraform.tfvars", items)

def normalize_workspace_url(url):
    if not url:
        return url
    if url.startswith("https://"):
        return url
    return f"https://{url}"

def read_env_file(path):
    values = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key] = value
    return values

def write_env_file(
    repo_root,
    openai_endpoint=None,
    openai_key=None,
    api_version=None,
    deployment_name=None,
    workspace_url=None,
):
    env_path = repo_root / ".env"
    values = read_env_file(env_path)
    if openai_endpoint is not None:
        values["OPENAI_API_BASE"] = openai_endpoint
    if openai_key is not None:
        values["OPENAI_API_KEY"] = openai_key
    if api_version is not None:
        values["OPENAI_API_VERSION"] = api_version
    if deployment_name is not None:
        values["OPENAI_DEPLOYMENT_NAME"] = deployment_name
    if workspace_url is not None:
        values["DATABRICKS_WORKSPACE_URL"] = normalize_workspace_url(workspace_url)
    if not values:
        return
    lines = [f"{key}={values[key]}" for key in ENV_KEYS if key in values]
    for key in sorted(values):
        if key in ENV_KEYS:
            continue
        lines.append(f"{key}={values[key]}")
    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

def set_databricks_kv_policy(vault_name):
    if AZ_BIN is None:
        raise FileNotFoundError("Azure CLI not found. Install Azure CLI or ensure az is on PATH.")
    run(
        [
            AZ_BIN,
            "keyvault",
            "set-policy",
            "--name",
            vault_name,
            "--spn",
            DATABRICKS_SP_APP_ID,
            "--secret-permissions",
            "get",
            "list",
        ]
    )

def set_key_vault_secret(vault_name, secret_name, secret_value):
    if secret_value is None:
        return
    if AZ_BIN is None:
        raise FileNotFoundError("Azure CLI not found. Install Azure CLI or ensure az is on PATH.")
    cmd = [
        AZ_BIN,
        "keyvault",
        "secret",
        "set",
        "--vault-name",
        vault_name,
        "--name",
        secret_name,
        "--value",
        secret_value,
    ]
    run_sensitive(cmd, redacted_indices=[len(cmd) - 1])

def sync_key_vault_secrets(vault_name, endpoint, api_key, api_version, deployment_name):
    set_key_vault_secret(vault_name, KEY_VAULT_SECRET_NAMES["OPENAI_API_BASE"], endpoint)
    set_key_vault_secret(vault_name, KEY_VAULT_SECRET_NAMES["OPENAI_API_KEY"], api_key)
    set_key_vault_secret(vault_name, KEY_VAULT_SECRET_NAMES["OPENAI_API_VERSION"], api_version)
    set_key_vault_secret(
        vault_name,
        KEY_VAULT_SECRET_NAMES["OPENAI_DEPLOYMENT_NAME"],
        deployment_name,
    )

def get_databricks_aad_token():
    if AZ_BIN is None:
        raise FileNotFoundError("Azure CLI not found. Install Azure CLI or ensure az is on PATH.")
    return run_capture(
        [
            AZ_BIN,
            "account",
            "get-access-token",
            "--resource",
            DATABRICKS_SP_APP_ID,
            "--query",
            "accessToken",
            "-o",
            "tsv",
        ]
    )

def normalize_databricks_host(host):
    if not host:
        return host
    return host if host.startswith("https://") else f"https://{host}"

def databricks_api(host, token, method, path, payload=None):
    url = f"{normalize_databricks_host(host).rstrip('/')}{path}"
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8")
        raise RuntimeError(f"Databricks API error {exc.code}: {detail}") from exc

def get_latest_model_version(host, token, model_name):
    paths = [
        ("/api/2.0/mlflow/registered-models/get-latest-versions", {"name": model_name}),
        ("/api/2.0/mlflow/model-versions/search", {"filter": f"name='{model_name}'"}),
        ("/api/2.0/preview/mlflow/model-versions/search", {"filter": f"name='{model_name}'"}),
    ]
    versions = []
    last_error = None
    for path, payload in paths:
        try:
            response = databricks_api(host, token, "POST", path, payload)
        except RuntimeError as exc:
            last_error = exc
            if "ENDPOINT_NOT_FOUND" in str(exc):
                continue
            raise
        items = response.get("model_versions", [])
        for item in items:
            version = item.get("version")
            if version is not None:
                try:
                    versions.append(int(version))
                except ValueError:
                    continue
        if versions:
            return str(max(versions))
    if last_error is not None and "ENDPOINT_NOT_FOUND" in str(last_error):
        return None
    if last_error is not None:
        raise last_error
    return None

if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser(description="Deploy Terraform stacks for Azure OpenAI and Databricks.")
        group = parser.add_mutually_exclusive_group()
        group.add_argument("--rg-only", action="store_true", help="Deploy only the resource group stack")
        group.add_argument("--openai-only", action="store_true", help="Deploy only the Azure OpenAI account stack")
        group.add_argument("--deployment-only", action="store_true", help="Deploy only the Azure OpenAI deployment stack")
        group.add_argument("--databricks-only", action="store_true", help="Deploy only the Databricks workspace stack")
        group.add_argument("--keyvault-only", action="store_true", help="Deploy only the Key Vault stack")
        group.add_argument("--compute-only", action="store_true", help="Deploy only the Databricks compute stack")
        group.add_argument("--notebooks-only", action="store_true", help="Deploy only the notebooks stack")
        group.add_argument("--serving-only", action="store_true", help="Deploy only the serving endpoint stack")
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
            write_rg_tfvars(rg_dir)
            run(["terraform", f"-chdir={rg_dir}", "init"])
            run(["terraform", f"-chdir={rg_dir}", "apply", "-auto-approve"])
            sys.exit(0)

        if args.openai_only:
            run(["terraform", f"-chdir={rg_dir}", "init"])
            rg_name = get_output(rg_dir, "resource_group_name")
            write_openai_tfvars(openai_dir, rg_name)
            run(["terraform", f"-chdir={openai_dir}", "init"])
            run(["terraform", f"-chdir={openai_dir}", "apply", "-auto-approve"])
            endpoint = get_output(openai_dir, "openai_endpoint")
            api_key = get_output_with_apply(openai_dir, "openai_primary_key")
            write_env_file(
                repo_root,
                openai_endpoint=endpoint,
                openai_key=api_key,
                api_version=DEFAULTS["openai_api_version"],
                deployment_name=DEFAULTS["deployment_name"],
            )
            sys.exit(0)

        if args.deployment_only:
            run(["terraform", f"-chdir={rg_dir}", "init"])
            rg_name = get_output(rg_dir, "resource_group_name")
            run(["terraform", f"-chdir={openai_dir}", "init"])
            account_name = get_output(openai_dir, "openai_account_name")
            account_id = get_output(openai_dir, "openai_account_id")
            endpoint = get_output(openai_dir, "openai_endpoint")
            api_key = get_output_with_apply(openai_dir, "openai_primary_key")
            write_deployment_tfvars(deployment_dir, rg_name, account_name)
            run(["terraform", f"-chdir={deployment_dir}", "init"])
            deployment_id = f"{account_id}/deployments/{DEFAULTS['deployment_name']}"
            run_apply_with_import(deployment_dir, deployment_id)
            write_env_file(
                repo_root,
                openai_endpoint=endpoint,
                openai_key=api_key,
                api_version=DEFAULTS["openai_api_version"],
                deployment_name=DEFAULTS["deployment_name"],
            )
            sys.exit(0)

        if args.databricks_only:
            run(["terraform", f"-chdir={rg_dir}", "init"])
            rg_name = get_output(rg_dir, "resource_group_name")
            write_databricks_tfvars(databricks_dir, rg_name)
            run(["terraform", f"-chdir={databricks_dir}", "init"])
            run(["terraform", f"-chdir={databricks_dir}", "apply", "-auto-approve"])
            workspace_url = get_output(databricks_dir, "databricks_workspace_url")
            write_env_file(repo_root, workspace_url=workspace_url)
            sys.exit(0)

        if args.keyvault_only:
            run(["terraform", f"-chdir={rg_dir}", "init"])
            rg_name = get_output(rg_dir, "resource_group_name")
            write_key_vault_tfvars(key_vault_dir, rg_name)
            run(["terraform", f"-chdir={key_vault_dir}", "init"])
            run(["terraform", f"-chdir={key_vault_dir}", "apply", "-auto-approve"])
            vault_name = get_output(key_vault_dir, "key_vault_name")
            set_databricks_kv_policy(vault_name)
            endpoint = get_output_optional(openai_dir, "openai_endpoint")
            api_key = get_output_optional(openai_dir, "openai_primary_key")
            if endpoint and api_key:
                sync_key_vault_secrets(
                    vault_name,
                    endpoint,
                    api_key,
                    DEFAULTS["openai_api_version"],
                    DEFAULTS["deployment_name"],
                )
            sys.exit(0)

        if args.compute_only:
            run(["terraform", f"-chdir={rg_dir}", "init"])
            rg_name = get_output(rg_dir, "resource_group_name")
            write_databricks_compute_tfvars(compute_dir, rg_name)
            run(["terraform", f"-chdir={compute_dir}", "init"])
            run(["terraform", f"-chdir={compute_dir}", "apply", "-auto-approve"])
            sys.exit(0)

        if args.notebooks_only:
            run(["terraform", f"-chdir={rg_dir}", "init"])
            rg_name = get_output(rg_dir, "resource_group_name")
            write_notebooks_tfvars(notebooks_dir, rg_name)
            run(["terraform", f"-chdir={notebooks_dir}", "init"])
            run(["terraform", f"-chdir={notebooks_dir}", "apply", "-auto-approve"])
            sys.exit(0)

        if args.serving_only:
            run(["terraform", f"-chdir={rg_dir}", "init"])
            rg_name = get_output(rg_dir, "resource_group_name")
            write_serving_tfvars(serving_dir, rg_name, databricks_dir)
            run(["terraform", f"-chdir={serving_dir}", "init"])
            run(["terraform", f"-chdir={serving_dir}", "apply", "-auto-approve"])
            sys.exit(0)

        write_rg_tfvars(rg_dir)
        run(["terraform", f"-chdir={rg_dir}", "init"])
        run(["terraform", f"-chdir={rg_dir}", "apply", "-auto-approve"])
        rg_name = get_output(rg_dir, "resource_group_name")

        write_openai_tfvars(openai_dir, rg_name)
        run(["terraform", f"-chdir={openai_dir}", "init"])
        run(["terraform", f"-chdir={openai_dir}", "apply", "-auto-approve"])
        account_name = get_output(openai_dir, "openai_account_name")
        account_id = get_output(openai_dir, "openai_account_id")
        endpoint = get_output(openai_dir, "openai_endpoint")
        api_key = get_output_with_apply(openai_dir, "openai_primary_key")

        write_deployment_tfvars(deployment_dir, rg_name, account_name)
        run(["terraform", f"-chdir={deployment_dir}", "init"])
        deployment_id = f"{account_id}/deployments/{DEFAULTS['deployment_name']}"
        run_apply_with_import(deployment_dir, deployment_id)

        write_databricks_tfvars(databricks_dir, rg_name)
        run(["terraform", f"-chdir={databricks_dir}", "init"])
        run(["terraform", f"-chdir={databricks_dir}", "apply", "-auto-approve"])
        workspace_url = get_output(databricks_dir, "databricks_workspace_url")

        write_key_vault_tfvars(key_vault_dir, rg_name)
        run(["terraform", f"-chdir={key_vault_dir}", "init"])
        run(["terraform", f"-chdir={key_vault_dir}", "apply", "-auto-approve"])
        vault_name = get_output(key_vault_dir, "key_vault_name")
        set_databricks_kv_policy(vault_name)
        sync_key_vault_secrets(
            vault_name,
            endpoint,
            api_key,
            DEFAULTS["openai_api_version"],
            DEFAULTS["deployment_name"],
        )

        write_databricks_compute_tfvars(compute_dir, rg_name)
        run(["terraform", f"-chdir={compute_dir}", "init"])
        run(["terraform", f"-chdir={compute_dir}", "apply", "-auto-approve"])

        write_notebooks_tfvars(notebooks_dir, rg_name)
        run(["terraform", f"-chdir={notebooks_dir}", "init"])
        run(["terraform", f"-chdir={notebooks_dir}", "apply", "-auto-approve"])
        write_env_file(
            repo_root,
            openai_endpoint=endpoint,
            openai_key=api_key,
            api_version=DEFAULTS["openai_api_version"],
            deployment_name=DEFAULTS["deployment_name"],
            workspace_url=workspace_url,
        )
    except subprocess.CalledProcessError as exc:
        print(f"Command failed: {exc}")
        sys.exit(exc.returncode)
