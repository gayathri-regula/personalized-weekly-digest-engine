import json
import urllib.request

BASE_URL = "https://personalized-weekly-digest-engine.onrender.com"

# Source of truth mapping from users.json
ORIGINAL_USERS = [
    {
        "id": "user_1",
        "name": "Alice Chen",
        "interest_tags": ["AI", "Machine Learning", "Python"],
    },
    {
        "id": "user_2",
        "name": "Bob Smith",
        "interest_tags": ["Mobile Development", "UI/UX Design", "Security"],
    },
    {
        "id": "user_3",
        "name": "Charlie Davis",
        "interest_tags": ["Cloud", "DevOps", "Backend Engineering"],
    },
    {
        "id": "user_4",
        "name": "Diana Prince",
        "interest_tags": ["JavaScript", "Open Source", "UI/UX Design"],
    },
    {
        "id": "user_5",
        "name": "Ethan Hunt",
        "interest_tags": ["Security", "Backend Engineering", "Open Source"],
    },
]

def make_request(url, method="GET", data=None):
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8") if data else None,
        headers={"Content-Type": "application/json"} if data else {},
        method=method,
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def main():
    print("=== Step 1: Restoring Original Interest Tags via PATCH /api/users/{user_id} ===")
    for u in ORIGINAL_USERS:
        user_id = u["id"]
        payload = {"interest_tags": u["interest_tags"]}
        patch_url = f"{BASE_URL}/api/users/{user_id}"
        print(f"PATCH {patch_url} -> {payload}")
        result = make_request(patch_url, method="PATCH", data=payload)
        print(f"Response ({user_id}): {json.dumps(result, indent=2)}\n")

    print("=== Step 2: Regenerating Weekly Digests via POST /api/digest/{user_id} ===")
    for u in ORIGINAL_USERS:
        user_id = u["id"]
        post_url = f"{BASE_URL}/api/digest/{user_id}"
        print(f"POST {post_url}")
        digest_res = make_request(post_url, method="POST")
        print(f"Digest Generated for {user_id}: id={digest_res['id']}, week={digest_res['week_identifier']}, generated_at={digest_res['generated_at']}\n")

    print("=== Step 3: Verifying Final State via GET /api/users ===")
    users_url = f"{BASE_URL}/api/users"
    all_users = make_request(users_url, method="GET")
    print(json.dumps(all_users, indent=2))

if __name__ == "__main__":
    main()
