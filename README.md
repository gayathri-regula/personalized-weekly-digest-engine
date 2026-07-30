# Personalized Weekly Digest Engine

[![Submission Document](https://img.shields.io/badge/Submission-SUBMISSION.md-blue.svg)](file:///c:/AI_Engineer/personalized-weekly-digest-engine/SUBMISSION.md)
[![Architecture Document](https://img.shields.io/badge/Architecture-ARCHITECTURE.md-green.svg)](file:///c:/AI_Engineer/personalized-weekly-digest-engine/ARCHITECTURE.md)
[![Backend Tests](https://img.shields.io/badge/Pytest-30%20Passing-success.svg)](backend/tests)

A personalized content aggregation and weekly digest engine that ranks user activity items according to interest profiles, recency decay, and engagement signals. It generates structured executive summary prose using Anthropic Claude 3.5 Sonnet (with a deterministic template fallback) and delivers periodic digest updates via a modern React web application.

---

## 1. Project Overview

The **Personalized Weekly Digest Engine** is an end-to-end AI-powered content delivery platform that solves developer information overload by aggregating weekly activity items and generating personalized executive digests. The platform is built across four core architectural pillars per the task specification:
1. **AI & Recommendation Engine**: Features a deterministic scoring ranker (60% tag match, 25% recency decay, 15% engagement) coupled with Anthropic Claude 3.5 Sonnet for executive summary prose composition (with a fallback to a template engine when unconfigured or offline).
2. **Backend API**: A high-performance Python 3.11 service built with FastAPI, SQLAlchemy 2.0 Async ORM, Pydantic v2, and PostgreSQL (Supabase) / SQLite database persistence.
3. **Frontend Web App**: A responsive, dark-mode glassmorphic dashboard built with React 18, Vite, TypeScript, and Vanilla CSS enabling multi-user profile switching and interactive digest generation.
4. **Deployment & Automation**: Live API hosted on Render free-tier, frontend deployed on Vercel, and automated recurring weekly batch digest regeneration executed via GitHub Actions (`.github/workflows/weekly_digest.yml`).

---

## 2. Live Deployment URLs

- **Frontend App**: [https://personalized-weekly-digest-engine-a.vercel.app](https://personalized-weekly-digest-engine-a.vercel.app)
- **Backend API**: [https://personalized-weekly-digest-engine.onrender.com](https://personalized-weekly-digest-engine.onrender.com)
- **Interactive Swagger Documentation**: [https://personalized-weekly-digest-engine.onrender.com/docs](https://personalized-weekly-digest-engine.onrender.com/docs)

> [!IMPORTANT]
> **Render Free-Tier Cold Start Delay**:  
> The backend web service is hosted on Render's free tier, which spins down after 15 minutes of inactivity. **The initial request after a period of inactivity (cold start) may take 30 to 50 seconds to respond** while the container spins up. Subsequent requests respond in ~100ms.

---

## 3. How the Ranker Decides Relevance ("Why" Note Mechanics)

### Scoring Formula
The ranker ([`backend/app/services/ranker.py`](backend/app/services/ranker.py)) assigns each activity item a composite `relevance_score` between `0.0` and `1.0`:

$$\text{relevance\_score} = 0.60 \times \text{tag\_score} + 0.25 \times \text{recency\_score} + 0.15 \times \text{engagement\_score}$$

1. **Tag Match Score (60% Weight)**: Ratio of matching user interest tags to total user tags ($\frac{|\text{UserInterests} \cap \text{ItemCategoryTags}|}{\max(1, |\text{UserInterests}|)}$).
2. **Recency Decay Score (25% Weight)**: Exponential decay $e^{-0.20 \times t_{\text{days}}}$ over elapsed days.
3. **Engagement Score (15% Weight)**: Normalized interaction score based on likes ($\times 2.0$), views ($\times 0.1$), and shares ($\times 5.0$).

### Explanation Generation & Fallback Rules
- **Direct Matching**: The `"because you follow X"` explanation is derived directly from the exact mathematical intersection of user interests and item tags ($\text{UserInterests} \cap \text{ItemCategoryTags}$) — it is not a separate invented sentence.
- **Minimum Relevance Threshold**: Items scoring below `0.10` are automatically excluded.
- **Zero-Overlap Fallback**: If an item has zero tag overlap with the user but qualifies based on high recency and engagement, it receives the fallback explanation: `"popular activity item in your network this week"`.

---

## 4. Multi-User Digest Validation Evidence

The engine delivers distinct, non-overlapping top activity items and personalized explanations across different user profiles based on live production API calculations:

| User Profile | User Interests | Top Ranked Highlight Item | Relevance Score | Explanation Text |
|---|---|---|---|---|
| **Alice Chen** (`user_1`) | `AI`, `Machine Learning`, `Python` | *Fine-Tuning Whisper for Multilingual Speech Recognition* | `0.8349` | `"because you follow AI, Machine Learning, Python"` |
| **Charlie Davis** (`user_3`) | `Cloud`, `DevOps`, `Backend Engineering` | *Kubernetes Operator Development with Go and Operator SDK* | `0.936` | `"because you follow Backend Engineering, Cloud, DevOps"` |
| **Diana Prince** (`user_4`) | `JavaScript`, `Open Source`, `UI/UX Design` | *Building Real-Time Chat UIs with WebSockets and React* | `0.7837` | `"because you follow JavaScript, UI/UX Design"` |

> **Why They Differ**: Alice, Charlie, and Diana have interest profiles with zero tag overlap by design. As a result, the tag intersection formula evaluates completely disjoint matching sets, surfacing tailored, domain-specific activity items for each user.

---

## 5. Scheduled Automation Job Evidence

Periodic digest generation is automated via GitHub Actions:
- **Workflow File**: [`.github/workflows/weekly_digest.yml`](.github/workflows/weekly_digest.yml)
- **Schedule**: Recurring cron trigger every Monday at 08:00 UTC (`0 8 * * 1`).
- **Manual Trigger**: Supports on-demand execution via `workflow_dispatch`.
- **Infrastructure Verification**: Verified running successfully on GitHub's infrastructure. The workflow uses `backend/scripts/regenerate_all_digests.py`, issuing a cold-start wake-up ping to Render before regenerating weekly digests for all platform users.

---

## 6. Architecture Summary

A detailed breakdown of system components, sequence diagrams, LLM fallback strategy, and database schema is available in [ARCHITECTURE.md](file:///c:/AI_Engineer/personalized-weekly-digest-engine/ARCHITECTURE.md).

---

## 7. Local Setup Instructions

Pointers to detailed setup guides:
- **Backend Setup**: See [`backend/README.md`](file:///c:/AI_Engineer/personalized-weekly-digest-engine/backend/README.md) (`pip install -r requirements.txt`, `python scripts/init_db.py`, `uvicorn app.main:app --reload`).
- **Frontend Setup**: See [`frontend/README.md`](file:///c:/AI_Engineer/personalized-weekly-digest-engine/frontend/README.md) (`npm install`, `npm run dev`).
- **Automated Tests**: Run `python -m pytest backend/tests -v` to execute all 30 unit & integration tests.

---

## 8. Known Limitations

- **Render Free-Tier Cold Start**: Cold start requests take 30–50 seconds when the server has been idle for over 15 minutes.
- **No User Authentication**: User switching is unauthenticated in the UI to simplify grading and evaluation.
- **Feedback-Link Stretch Goal**: Direct feedback links (like/dislike feedback per item) were an optional stretch goal and are not included in this release.
