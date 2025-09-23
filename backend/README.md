# Shorty+QR (Backend Only)

This is a minimal FastAPI + SQLite backend for creating short links, redirecting, and serving QR codes.

## Quickstart

### 1) Create and activate a virtual environment
**macOS/Linux**
```bash
python3 -m venv .venv
source .venv/bin/activate
```
**Windows (PowerShell)**
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2) Install dependencies
```bash
pip install -r backend/requirements.txt
```

### 3) Run the server
```bash
cd backend
uvicorn app:app --reload --port 8080
```

You should see: `Uvicorn running on http://127.0.0.1:8080`

### 4) Try the API (in a new terminal)
Create a link:
```bash
curl -s -X POST http://localhost:8080/api/links -H "Content-Type: application/json" -d '{ "url": "https://example.com" }' | jq
```

List links:
```bash
curl -s http://localhost:8080/api/links | jq
```

Open a redirect in your browser (replace `abc123` with your slug):
```
http://localhost:8080/r/abc123
```

Get a QR image for a slug:
```
http://localhost:8080/api/links/abc123/qr
```

## Notes
- The SQLite file is created at `backend/data/shorty.db`.
- CORS is open to make the React frontend easier later.
