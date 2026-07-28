# Personalized Weekly Digest Engine - Backend

Python FastAPI backend service for activity ranking, summarization, and digest delivery.

## Local Development Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. (Optional) Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. Install backend dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the FastAPI development server:
   ```bash
   uvicorn app.main:app --reload
   ```

5. Verify server status by accessing the health endpoint:
   - Endpoint: `http://127.0.0.1:8000/health`
   - Expected Response: `{"status": "ok"}`
