# JusticeFlow MVP — Frontend (Phase A/B)

## 1. Install dependencies

```bash
cd frontend
npm install
```

## 2. Run the dev server

```bash
npm run dev
```

Open http://localhost:5174

## 3. Verify Phase B end-to-end

Make sure the backend is running on http://localhost:8000 first.

1. Type: `My Honda Activa was stolen yesterday evening near my college.`
2. Click "Analyze Complaint".
3. You should see the complaint type, summary, and extracted
   entities (with `vehicle_registration_number` and
   `complainant_name` as `null`, since they weren't mentioned).

If the backend isn't running or Gemini isn't configured, you'll see
a clean error message on the page instead of a crash.
