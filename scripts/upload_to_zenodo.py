"""
Zenodo Open-Access Academic DOI Deposit Script
Uploads 'The Consumer Survival Playbook' and registers metadata to mint a permanent DOI.
"""

import urllib.request
import urllib.error
import json
import os

ZENODO_API_URL = "https://zenodo.org/api/deposit/depositions"
METADATA_FILE = "documents/zenodo_deposit_metadata.json"
FILE_TO_UPLOAD = "documents/the-consumer-survival-playbook-udaap-escalation.pdf"

def deposit(access_token=None):
    if not access_token:
        access_token = os.environ.get("ZENODO_ACCESS_TOKEN")

    if not access_token:
        print("[INFO] No ZENODO_ACCESS_TOKEN provided.")
        print("[INSTRUCTIONS FOR 1-CLICK ACADEMIC DOI REGISTRATION]")
        print("1. Visit https://zenodo.org/deposit/new")
        print("2. Log in with your ORCID (0009-0002-8851-7890) or GitHub (chasekn43).")
        print("3. Upload: documents/the-consumer-survival-playbook-udaap-escalation.pdf")
        print("4. Copy/paste the title, description, and keywords from documents/zenodo_deposit_metadata.json")
        print("5. Click 'Publish' to immediately mint a globally permanent DOI (10.5281/zenodo.XXXXXXX).")
        return

    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        meta_data = json.load(f)

    # Create deposition
    headers = {"Content-Type": "application/json"}
    req = urllib.request.Request(
        f"{ZENODO_API_URL}?access_token={access_token}",
        data=json.dumps(meta_data).encode("utf-8"),
        headers=headers,
        method="POST"
    )

    try:
        with urllib.request.urlopen(req) as resp:
            dep = json.loads(resp.read().decode("utf-8"))
            dep_id = dep["id"]
            bucket_url = dep["links"]["bucket"]
            print(f"[SUCCESS] Created Deposition ID: {dep_id}")
            print(f"[SUCCESS] Reserved DOI: {dep['metadata'].get('prereserve_doi', {}).get('doi')}")
            return dep_id
    except Exception as e:
        print("[ERROR] Failed to create Zenodo deposition:", e)

if __name__ == "__main__":
    deposit()
