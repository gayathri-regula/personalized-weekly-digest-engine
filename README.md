# Personalized Weekly Digest Engine

A personalized content aggregation and weekly digest engine that ranks user activity items according to interest profiles, recency decay, and engagement signals. It generates structured executive summary prose using Claude 3.5 Sonnet (with a deterministic template fallback) and delivers periodic digest updates via a modern React web application.

---

## 1. Setup & Run Instructions

### Prerequisites
- **Backend**: Python 3.11 or 3.12 installed.
- **Frontend**: Node.js 18+ and npm installed.

### A. Environment Configuration
Create a `.env` file in the `backend/` directory based on `.env.example`:
```bash
cd backend
cp .env.example .env
```
Ensure required environment variables are set in `backend/.env`:
- `DATABASE_URL`: Supabase PostgreSQL connection URI (`postgresql+asyncpg://...`)
- `ANTHROPIC_API_KEY`: Anthropic API key for Claude 3.5 Sonnet summarization (optional; system falls back to template summarizer if empty)
- `DEFAULT_SUMMARIZER_PROVIDER`: Default AI model identifier (`"claude-sonnet-4-6"`)
- `SERVICE_NAME`: Service registration identifier (`"weekly-digest-api"`)

> **Note**: Never expose real credentials or API keys in repository commits.

### B. Backend Local Setup & Server Run
```bash
# Navigate to backend directory
cd backend

# Install Python dependencies
pip install -r requirements.txt

# (Optional) Seed/Initialize local or remote database
python scripts/init_db.py
python scripts/load_dataset.py

# Launch FastAPI development server with uvicorn
uvicorn app.main:app --reload --port 8000
```
Verify the server is running by opening `http://127.0.0.1:8000/health` in your browser or executing `curl http://127.0.0.1:8000/health`.

### C. Frontend Local Setup & Run
```bash
# Navigate to frontend directory in a separate terminal
cd frontend

# Install Node modules
npm install

# Start Vite development server
npm run dev
```
Open your browser at `http://localhost:5173` to interact with the application.

### D. Running the Test Suite
Run all unit and integration tests (30 passing tests) across ranker, summarizer, service, and API layers:
```bash
python -m pytest backend/tests -v
```

---

## 2. System Architecture

The project is structured with a strict separation of concerns between recommendation scoring, AI summarization, data persistence, and UI presentation:

- **Ranker vs. Summarizer Separation**: The rule-based deterministic ranker (`backend/app/services/ranker.py`) scores, filters, and ranks activity items first. The AI summarizer module (`backend/app/services/summarizer.py`) then receives the top-ranked items to compose structured executive prose.
- **Backend Stack**: Built with **Python 3.11**, **FastAPI** for REST API endpoints, **SQLAlchemy 2.0** (AsyncSession), **Pydantic v2** & `pydantic-settings` for configuration management, and **Uvicorn** as the ASGI server.
- **Frontend Stack**: Built with **React 18**, **Vite**, **TypeScript**, and **Vanilla CSS** with glassmorphism and modern dark-mode aesthetic styling.
- **Database Layer**: **Supabase PostgreSQL** accessed via `asyncpg` in production, with an in-memory SQLite database (`aiosqlite`) for fast, isolated automated testing.
- **Hosting & Infrastructure**:
  - **Backend**: Hosted on **Render** as a Python Web Service.
  - **Frontend**: Deployed on **Vercel** static site hosting.

---

## 3. Live Deployment Links

- **Frontend App**: [https://personalized-weekly-digest-engine-a.vercel.app](https://personalized-weekly-digest-engine-a.vercel.app)
- **Backend API**: [https://personalized-weekly-digest-engine-1.onrender.com](https://personalized-weekly-digest-engine-1.onrender.com)
- **Interactive Swagger Documentation**: [https://personalized-weekly-digest-engine-1.onrender.com/docs](https://personalized-weekly-digest-engine-1.onrender.com/docs)

> **Important Note**: The backend web service is hosted on Render's free tier, which spins down after 15 minutes of inactivity. The initial request after an idle period (cold start) may take **50+ seconds** to respond while the container spins up.

---

## 4. Ranker Relevance Logic

The deterministic activity recommendation engine is implemented in [`backend/app/services/ranker.py`](backend/app/services/ranker.py) (specifically within functions `rank_items_for_user`, `compute_tag_match_score`, `compute_recency_decay`, and `compute_engagement_score`).

### Scoring Formula
Each activity item is assigned a composite `relevance_score` between `0.0` and `1.0` calculated as a weighted sum of three independent signals:

$$\text{relevance\_score} = 0.60 \times \text{tag\_score} + 0.25 \times \text{recency\_score} + 0.15 \times \text{engagement\_score}$$

1. **Interest-Tag Match Score ($60\%$ weight)**:
   - **Code Reference**: `compute_tag_match_score()` in [`ranker.py`](backend/app/services/ranker.py#L44-L67).
   - **Formula**: $\frac{|\text{UserInterests} \cap \text{ItemCategoryTags}|}{\max(1, |\text{UserInterests}|)}$
   - Measures the proportion of the user's explicit interest tags present on the item.
2. **Recency Decay Score ($25\%$ weight)**:
   - **Code Reference**: `compute_recency_decay()` in [`ranker.py`](backend/app/services/ranker.py#L69-L96).
   - **Formula**: $e^{-\lambda \cdot t_{\text{days}}}$ where $\lambda = 0.20$.
   - An exponential decay where an item 7 days old retains $\approx 24.7\%$ of its recency value.
3. **Engagement Score ($15\%$ weight)**:
   - **Code Reference**: `compute_engagement_score()` in [`ranker.py`](backend/app/services/ranker.py#L99-L121).
   - **Formula**: $\min\left(1.0, \frac{\text{likes} \times 2.0 + \text{views} \times 0.1 + \text{shares} \times 5.0}{100.0}\right)$
   - Normalizes raw user interaction metrics to a $[0.0, 1.0]$ scale.

### Threshold & Sorting
- Items with a final `relevance_score` strictly below `0.10` (`MIN_RELEVANCE_THRESHOLD`) are excluded.
- The remaining items are sorted descending by `relevance_score` (with creation timestamp and item ID as tie-breakers) and capped to the top $N$ items (default: 5).

---

## 5. "Why" Explanation Mechanism

The human-readable explanation line associated with each highlight item (`explanation_text`) is computed in `derive_explanation()` in [`backend/app/services/ranker.py`](backend/app/services/ranker.py#L123-L137).

### Personalization & Truthfulness
- **Intersection Logic**: `explanation_text` is constructed by computing the **exact mathematical intersection** between the item's `category_tags` and the target user's `interest_tags`:
  $$\text{MatchingTags} = \text{UserInterests} \cap \text{ItemCategoryTags}$$
- If matching tags exist, the explanation formats them into a statement: `"because you follow TagA, TagB"`.
- **Truthful vs. Decorative**: The system does **not** simply print all of an item's tags. For instance, if an activity item has tags `["AI", "Machine Learning", "Python"]`:
  - **User 1** (following `AI`, `Machine Learning`, `Python`) receives: `"because you follow AI, Machine Learning, Python"`.
  - **User A** (following `AI`, `Cloud`) receives: `"because you follow AI"`.
  - **User B** (following `Python`, `Backend Engineering`) receives: `"because you follow Python"`.
- This guarantees that two users viewing the exact same activity item will see different, truthful explanations matching their personal profile.
- **Fallback**: If an item qualifies based on high recency and engagement despite zero tag overlap, it displays `"popular activity item in your network this week"`.

---

## 6. GitHub Actions Automated Scheduler

Periodic weekly digest generation is automated via a GitHub Actions workflow:

- **Workflow Path**: [`.github/workflows/weekly_digest.yml`](.github/workflows/weekly_digest.yml)
- **Schedule (Cron)**: Executed automatically every Monday at 09:00 UTC (`cron: '0 9 * * 1'`), with support for manual triggers via `workflow_dispatch`.
- **Execution Workflow**: Runs `backend/scripts/regenerate_all_digests.py`, which executes an automated 90-second wake-up ping against `GET /health` to wake Render from free-tier sleep before sequentially invoking `POST /api/digest/{user_id}` for all registered users.
- **Verification Evidence**: Complete run history, timing, and step execution logs can be reviewed under the repository's **Actions** tab on GitHub.

---

## 7. Multi-User Validation Evidence

The personalization engine has been validated against three distinct seed users, confirming 100% non-overlapping, domain-specific digest outputs:

| User ID | User Name | Interest Tags | Primary Digest Topic Cluster | Top Ranked Highlight Item |
|---|---|---|---|---|
| `user_1` | **Alice Chen** | `AI`, `Machine Learning`, `Python` | **AI/ML & LLM Optimization** | *Fine-Tuning Whisper for Multilingual Speech Recognition* (Score: `0.8349`) |
| `user_2` | **Bob Smith** | `Mobile Development`, `UI/UX Design`, `Security` | **Mobile Security & Interactive UIs** | *Securing Biometric Authentication on Android and iOS* (Score: `0.7838`) |
| `user_3` | **Charlie Davis** | `Cloud`, `DevOps`, `Backend Engineering` | **Cloud Infrastructure & Kubernetes** | *Kubernetes Operator Development with Go and Operator SDK* (Score: `0.9360`) |
