"""Weekly batch digest regeneration script for scheduled execution in CI/CD (GitHub Actions)."""

import os
import sys
from typing import Any, Dict, List
import httpx


def main() -> None:
    """Fetch all users and trigger digest regeneration for each user sequentially."""
    backend_base_url = os.getenv("BACKEND_BASE_URL", "").strip()

    if not backend_base_url:
        print("[ERROR] BACKEND_BASE_URL environment variable is required.")
        print("Example: BACKEND_BASE_URL=http://127.0.0.1:8000 python backend/scripts/regenerate_all_digests.py")
        sys.exit(1)

    # Normalize URL (remove trailing slash)
    backend_url = backend_base_url.rstrip("/")

    print(f"==========================================")
    print(f"Starting Weekly Batch Digest Regeneration")
    print(f"Target Backend URL: {backend_url}")
    print(f"==========================================\n")

    # 1. Fetch user list from backend API
    try:
        with httpx.Client(timeout=30.0) as client:
            print(f"[STEP 1] Fetching user list from {backend_url}/api/users...")
            users_res = client.get(f"{backend_url}/api/users")
            if users_res.status_code != 200:
                print(f"[ERROR] Failed to fetch users list: HTTP {users_res.status_code} - {users_res.text[:200]}")
                sys.exit(1)

            users_data: Dict[str, Any] = users_res.json()
            users: List[Dict[str, Any]] = users_data.get("users", [])

            if not users:
                print("[INFO] Zero users found in database. Exiting successfully.")
                sys.exit(0)

            print(f"[INFO] Found {len(users)} users. Beginning batch digest generation...\n")

            succeeded_count = 0
            failed_count = 0

            # 2. Iterate through each user and trigger POST /api/digest/{user_id}
            for idx, user in enumerate(users, start=1):
                user_id = user.get("id", "unknown")
                user_name = user.get("name", "Unknown User")

                print(f"[{idx}/{len(users)}] Regenerating digest for user '{user_name}' (ID: {user_id})...")

                try:
                    digest_res = client.post(f"{backend_url}/api/digest/{user_id}")
                    if digest_res.status_code == 200:
                        digest_data = digest_res.json()
                        week_id = digest_data.get("week_identifier", "N/A")
                        items_count = len(digest_data.get("items", []))
                        print(
                            f"  --> [SUCCESS] Digest compiled for week {week_id} with {items_count} items."
                        )
                        succeeded_count += 1
                    else:
                        print(
                            f"  --> [FAILURE] HTTP {digest_res.status_code}: {digest_res.text[:200]}"
                        )
                        failed_count += 1
                except Exception as req_err:
                    print(f"  --> [FAILURE] Network/Timeout error: {req_err}")
                    failed_count += 1

            # 3. Output summary results and set exit code
            print(f"\n==========================================")
            print(f"DIGEST REGENERATION BATCH SUMMARY")
            print(f"Total Users Target:    {len(users)}")
            print(f"Succeeded:             {succeeded_count}")
            print(f"Failed:                {failed_count}")
            print(f"==========================================")

            if failed_count > 0:
                print(f"[ERROR] {failed_count} user digest regeneration(s) failed.")
                sys.exit(1)
            else:
                print("[SUCCESS] All user digests successfully regenerated!")
                sys.exit(0)

    except Exception as exc:
        print(f"[ERROR] Unexpected fatal failure connecting to backend URL '{backend_url}': {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
