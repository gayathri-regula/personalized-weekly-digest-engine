"""QA Final Verification Script for Live Production System.

Performs 10 end-to-end checks against live Vercel frontend and Render backend API.
"""

import sys
import httpx

FRONTEND_URL = "https://personalized-weekly-digest-engine-a.vercel.app"
BACKEND_URL = "https://personalized-weekly-digest-engine.onrender.com"


def run_qa_suite() -> int:
    passed_count = 0
    failed_count = 0

    print("==========================================")
    print("STARTING LIVE QA FINAL VERIFICATION SUITE")
    print(f"Backend Target:  {BACKEND_URL}")
    print(f"Frontend Target: {FRONTEND_URL}")
    print("==========================================\n")

    with httpx.Client(timeout=90.0) as client:
        # CHECK 1 - Backend Health
        try:
            res1 = client.get(f"{BACKEND_URL}/health")
            if res1.status_code == 200 and res1.json().get("status") == "ok":
                print("[PASS] Check 1: Backend health endpoint returned HTTP 200 status 'ok'.")
                passed_count += 1
            else:
                print(f"[FAIL] Check 1: Backend health returned HTTP {res1.status_code} - {res1.text[:100]}")
                failed_count += 1
        except Exception as err:
            print(f"[FAIL] Check 1: Backend health request error - {err}")
            failed_count += 1

        # CHECK 2 - Frontend Reachable
        try:
            res2 = client.get(FRONTEND_URL)
            if res2.status_code == 200:
                print("[PASS] Check 2: Live Frontend application is reachable (HTTP 200).")
                passed_count += 1
            else:
                print(f"[FAIL] Check 2: Frontend returned HTTP {res2.status_code}")
                failed_count += 1
        except Exception as err:
            print(f"[FAIL] Check 2: Frontend request error - {err}")
            failed_count += 1

        # CHECK 3 - Users Endpoint
        users = []
        try:
            res3 = client.get(f"{BACKEND_URL}/api/users")
            if res3.status_code == 200:
                users_data = res3.json().get("users", [])
                if len(users_data) == 5 and all(u.get("id") and u.get("name") and u.get("interest_tags") for u in users_data):
                    users = users_data
                    print(f"[PASS] Check 3: Users endpoint returned exactly {len(users_data)} valid users.")
                    passed_count += 1
                else:
                    print(f"[FAIL] Check 3: Expected 5 complete users, got {len(users_data)}")
                    failed_count += 1
            else:
                print(f"[FAIL] Check 3: Users endpoint returned HTTP {res3.status_code}")
                failed_count += 1
        except Exception as err:
            print(f"[FAIL] Check 3: Users endpoint request error - {err}")
            failed_count += 1

        # CHECK 4 - Non-overlapping Interest Tags across Demo Users (user_1, user_2, user_3)
        try:
            u_map = {u["id"]: set(u["interest_tags"]) for u in users}
            u1_tags = u_map.get("user_1", set())
            u2_tags = u_map.get("user_2", set())
            u3_tags = u_map.get("user_3", set())

            p1_2 = u1_tags & u2_tags
            p1_3 = u1_tags & u3_tags
            p2_3 = u2_tags & u3_tags

            print(f"  Intersection user_1 & user_2: {p1_2}")
            print(f"  Intersection user_1 & user_3: {p1_3}")
            print(f"  Intersection user_2 & user_3: {p2_3}")

            if p1_2 == set() and p1_3 == set() and p2_3 == set():
                print("[PASS] Check 4: Demo users (user_1, user_2, user_3) have zero overlapping interest_tags.")
                passed_count += 1
            else:
                print(f"[FAIL] Check 4: Interest tags overlap detected! {p1_2}, {p1_3}, {p2_3}")
                failed_count += 1
        except Exception as err:
            print(f"[FAIL] Check 4: Interest tag evaluation error - {err}")
            failed_count += 1

        # CHECK 5 - Digest Generation for All 5 Users
        digest_responses = {}
        ch5_success = True
        try:
            for u in users:
                uid = u["id"]
                res5 = client.post(f"{BACKEND_URL}/api/digest/{uid}")
                if res5.status_code == 200:
                    d_data = res5.json()
                    items = d_data.get("items", [])
                    if items and all(it.get("explanation_text") for it in items):
                        digest_responses[uid] = d_data
                    else:
                        ch5_success = False
                        print(f"  [ERROR] User {uid} digest items invalid or missing explanations.")
                else:
                    ch5_success = False
                    print(f"  [ERROR] User {uid} digest POST returned HTTP {res5.status_code}")

            if ch5_success and len(digest_responses) == 5:
                print(f"[PASS] Check 5: Successfully generated digests for all 5 users with valid items & explanations.")
                passed_count += 1
            else:
                print("[FAIL] Check 5: Failed to generate valid digests for all 5 users.")
                failed_count += 1
        except Exception as err:
            print(f"[FAIL] Check 5: Digest generation error - {err}")
            failed_count += 1

        # CHECK 6 - Truthful Explanations Verification
        ch6_success = True
        ch6_failures = []
        try:
            for u in users:
                uid = u["id"]
                user_interests_lower = {t.lower() for t in u["interest_tags"]}
                d_data = digest_responses.get(uid, {})
                for item in d_data.get("items", []):
                    exp = item.get("explanation_text", "")
                    if exp.startswith("because you follow"):
                        listed_tags_str = exp[len("because you follow"):].strip()
                        listed_tags = [t.strip() for t in listed_tags_str.split(",")]
                        item_tags_lower = {t.lower() for t in item.get("category_tags", [])}

                        for tag in listed_tags:
                            tag_lower = tag.lower()
                            if tag_lower not in user_interests_lower:
                                ch6_success = False
                                ch6_failures.append(f"User {uid} item '{item.get('title')}' lists tag '{tag}' not in user interests {u['interest_tags']}")
                            if tag_lower not in item_tags_lower:
                                ch6_success = False
                                ch6_failures.append(f"User {uid} item '{item.get('title')}' lists tag '{tag}' not in item category tags {item.get('category_tags')}")

            if ch6_success:
                print("[PASS] Check 6: All 'because you follow X' explanations accurately match both user interests & item tags.")
                passed_count += 1
            else:
                print(f"[FAIL] Check 6: Explanation tag mismatch detected - {'; '.join(ch6_failures)}")
                failed_count += 1
        except Exception as err:
            print(f"[FAIL] Check 6: Explanation verification error - {err}")
            failed_count += 1

        # CHECK 7 - Distinct Top Items Across Demo Trio (user_1, user_3, user_4)
        try:
            u1_top = digest_responses.get("user_1", {}).get("items", [{}])[0].get("activity_item_id")
            u3_top = digest_responses.get("user_3", {}).get("items", [{}])[0].get("activity_item_id")
            u4_top = digest_responses.get("user_4", {}).get("items", [{}])[0].get("activity_item_id")

            print(f"  user_1 top item: {u1_top}")
            print(f"  user_3 top item: {u3_top}")
            print(f"  user_4 top item: {u4_top}")

            if u1_top and u3_top and u4_top and u1_top != u3_top and u1_top != u4_top and u3_top != u4_top:
                print("[PASS] Check 7: Demo trio (user_1, user_3, user_4) produced genuinely distinct top-ranked items.")
                passed_count += 1
            else:
                print(f"[FAIL] Check 7: Top items are not distinct across demo trio ({u1_top}, {u3_top}, {u4_top}).")
                failed_count += 1
        except Exception as err:
            print(f"[FAIL] Check 7: Top item comparison error - {err}")
            failed_count += 1

        # CHECK 8 - GET Persistence Consistency
        try:
            posted_id = digest_responses.get("user_1", {}).get("id")
            res8 = client.get(f"{BACKEND_URL}/api/digest/user_1")
            if res8.status_code == 200:
                fetched_id = res8.json().get("id")
                if fetched_id == posted_id:
                    print(f"[PASS] Check 8: GET after POST returned consistent persistent digest ID '{fetched_id}'.")
                    passed_count += 1
                else:
                    print(f"[FAIL] Check 8: Digest ID mismatch between POST ('{posted_id}') and GET ('{fetched_id}')")
                    failed_count += 1
            else:
                print(f"[FAIL] Check 8: GET /api/digest/user_1 returned HTTP {res8.status_code}")
                failed_count += 1
        except Exception as err:
            print(f"[FAIL] Check 8: GET persistence check error - {err}")
            failed_count += 1

        # CHECK 9 - Nonexistent User Returns 404
        try:
            res9 = client.post(f"{BACKEND_URL}/api/digest/does_not_exist_12345")
            if res9.status_code == 404:
                print("[PASS] Check 9: Nonexistent user POST returned HTTP 404 Not Found as expected.")
                passed_count += 1
            else:
                print(f"[FAIL] Check 9: Expected HTTP 404, got HTTP {res9.status_code}")
                failed_count += 1
        except Exception as err:
            print(f"[FAIL] Check 9: Nonexistent user test error - {err}")
            failed_count += 1

        # CHECK 10 - Correct Week Identifier ("2026-W30")
        try:
            weeks = [d.get("week_identifier") for d in digest_responses.values()]
            if all(w == "2026-W30" for w in weeks):
                print(f"[PASS] Check 10: All digest responses report correct week_identifier '2026-W30'.")
                passed_count += 1
            else:
                print(f"[FAIL] Check 10: Week identifier mismatch detected in {weeks}")
                failed_count += 1
        except Exception as err:
            print(f"[FAIL] Check 10: Week identifier check error - {err}")
            failed_count += 1

    print("\n==========================================")
    print(f"QA SUMMARY: {passed_count}/10 checks passed")
    print("==========================================")

    return 0 if failed_count == 0 else 1


if __name__ == "__main__":
    sys.exit(run_qa_suite())
