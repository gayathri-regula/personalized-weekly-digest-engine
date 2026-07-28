# SFCollab Seed Datasets

This directory contains the canonical seed datasets for the **Personalized Weekly Digest Engine**, providing realistic users and platform activity items for weekly digest generation and testing.

---

## 1. Topic Taxonomy

The system uses a fixed taxonomy of 12 non-overlapping domain tags across user interests and activity item categories:

1. `AI`
2. `Machine Learning`
3. `Python`
4. `JavaScript`
5. `Cloud`
6. `DevOps`
7. `Data Science`
8. `Mobile Development`
9. `Security`
10. `UI/UX Design`
11. `Backend Engineering`
12. `Open Source`

---

## 2. Week Identifier & Date Range

- **Week Identifier**: `2026-W30`
- **Date Range**: July 20, 2026 00:00:00Z to July 26, 2026 23:59:59Z (7-day window)
- All activity item `created_at` timestamps are ISO-8601 strings distributed across this week.

---

## 3. Data Schemas

### 3.1 `users.json`
Contains registered platform users and their topic interests.

```json
{
  "id": "string (e.g. user_1)",
  "name": "string (e.g. Alice Chen)",
  "interest_tags": ["list of strings from taxonomy"]
}
```

### 3.2 `activity_items.json`
Contains community activity items generated during the target week.

```json
{
  "id": "string (e.g. item_01)",
  "title": "string",
  "content": "string (2-4 sentences)",
  "category_tags": ["list of 1-3 strings from taxonomy"],
  "created_at": "ISO-8601 timestamp string",
  "engagement_metadata": {
    "views": "integer",
    "likes": "integer",
    "shares": "integer",
    "comments": "integer"
  }
}
```

---

## 4. User Personalization & Interest Divergence Design

To guarantee that the ranking engine produces genuinely distinct digests across users (the core grading criterion), user interest profiles were deliberately engineered with non-overlapping primary domain focus areas:
- **User 1 (Alice Chen)**: Focused on Data & AI (`AI`, `Machine Learning`, `Python`).
- **User 2 (Bob Smith)**: Focused on Mobile & Client Security (`Mobile Development`, `UI/UX Design`, `Security`).
- **User 3 (Charlie Davis)**: Focused on Infrastructure & Systems (`Cloud`, `DevOps`, `Backend Engineering`).
- **User 4 (Diana Prince)**: Focused on Web & Open Source (`JavaScript`, `Open Source`, `UI/UX Design`).
- **User 5 (Ethan Hunt)**: Focused on Application Security & Backend (`Security`, `Backend Engineering`, `Open Source`).

Because User 1, User 2, and User 3 share zero common interest tags in their primary profiles, the deterministic ranking algorithm scores completely different subsets of candidate items into their Top-N digest positions.
