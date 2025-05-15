import json
import re
import subprocess
import os

# === Editable path to Sui client binary ===
SUI_BIN = "/opt/homebrew/Cellar/sui/1.48.1/bin/sui"

# Constants to extract
search_map = {
    "PYTH_EXAMPLE_PACKAGE_ID": {"published": True, "module": "consts"},
}

def load_deploy_json(filename):
    with open(filename, "r") as f:
        return json.load(f)

def get_object_ids(data):
    result = {}
    for constant, criteria in search_map.items():
        if criteria.get("published"):
            for change in data.get("objectChanges", []):
                if change.get("type") == "published":
                    if criteria["module"] in change.get("modules", []):
                        result[constant] = change.get("packageId")
                        break
        elif "pattern" in criteria:
            pattern = criteria["pattern"]
            for change in data.get("objectChanges", []):
                obj_type = change.get("objectType", "")
                if re.search(pattern, obj_type):
                    result[constant] = change.get("objectId")
                    break
    return result

def save_to_env_file(object_ids, filename=".env"):
    with open(filename, "w") as f:
        for key, value in object_ids.items():
            os.environ[key] = value
            f.write(f"{key}={value}\n")

def main():
    # Step 1: Switch to testnet environment
    subprocess.run([SUI_BIN, "client", "switch", "--env", "testnet"], check=True)

    # Step 2: Change to the correct directory
    os.chdir("../packages/pyth_example")

    # Step 3: Build publish command
    cmd = [
        SUI_BIN, "client", "publish",
        "--skip-dependency-verification",
        "--skip-fetch-latest-git-deps",
        "--silence-warnings",
        "--gas-budget", "1000000000",
        "--json"
    ]

    # Step 4: Run publish command, capture output
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    # Step 5: Save stdout to file
    with open("deploy.json", "w") as f:
        f.write(result.stdout)

    # Step 6: Check for errors
    if result.returncode != 0:
        print("❌ Error during publishing:")
        print(result.stderr)
        exit(1)

    # Step 7: Parse deploy.json and extract relevant IDs
    data = load_deploy_json("deploy.json")
    object_ids = get_object_ids(data)

    # Step 8: Save to .env
    save_to_env_file(object_ids)

    # Step 9: Display results
    for key in object_ids:
        print(f"FOUND: {key}={object_ids[key]}")

if __name__ == "__main__":
    main()
