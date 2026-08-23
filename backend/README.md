# JusticeFlow MVP — Backend (Phase A/B)

## 1. Create and activate a virtual environment

```bash
cd backend
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
```

## 2. Install dependencies

```bash
pip install -r requirements.txt
```

## 3. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in:
- `DATABASE_URL` — your local PostgreSQL connection string
- `GEMINI_API_KEY` — your Gemini API key (never commit this)

## 4. Create the PostgreSQL database

```bash
psql -U postgres -c "CREATE DATABASE justiceflow;"
psql -U postgres -c "CREATE USER justiceflow_user WITH PASSWORD 'justiceflow_pass';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE justiceflow TO justiceflow_user;"
```

(Adjust names/passwords to match whatever you put in `.env`.)

Tables are created automatically on startup (`Base.metadata.create_all`)
— no Alembic migrations for this MVP. The `complaints` table is the
source of truth for case records and case IDs (e.g. `JF-000001`); the
frontend never generates a case ID itself.

## 5. Run the server

```bash
uvicorn app.main:app --reload --port 8000
```

## 6. Verify Phase A

```bash
curl http://localhost:8000/health
# {"status":"ok"}
```

## 7. Verify Phase B

```bash
curl -X POST http://localhost:8000/complaints/analyze \
  -H "Content-Type: application/json" \
  -d '{"complaint_text": "My Honda Activa was stolen yesterday evening near my college."}'
```

You should get back JSON with `complaint_type`, `summary`, and `entities`.
If `GEMINI_API_KEY` isn't set or is invalid, you'll get a clean 503
error instead of a crash — that's expected and correct behavior.

## 8. Verify the complaint record endpoints (real DB, no mock data)

```bash
# Should be empty on a fresh database
curl http://localhost:8000/complaints

# Create a record (this is what the frontend's Review page submits)
curl -X POST http://localhost:8000/complaints \
  -H "Content-Type: application/json" \
  -d '{
        "complaint_type": "vehicle_theft",
        "complaint_text": "My Honda Activa was stolen yesterday evening near my college parking area.",
        "summary": "The complainant reported that their Honda Activa was stolen near their college.",
        "structured_data": {"complainant_name": "Abi", "vehicle_registration_number": "TN09AB1234"}
      }'
# -> returns the full record including a real, DB-generated case_id like "JF-000001"

# List should now include it
curl http://localhost:8000/complaints

# Fetch by case_id
curl http://localhost:8000/complaints/JF-000001
```

## What's NOT here yet (by design)

Per the phased plan: no case correlation engine, no auth, no officer
review workflow beyond a status field. Those are Phase G/H onward.
