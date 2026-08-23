## Running JusticeFlow

### Backend

cd backend

Activate the virtual environment (Windows PowerShell):
.\venv\Scripts\Activate.ps1

Install dependencies (first time only):
pip install -r requirements.txt

Create backend/.env:
DATABASE_URL=your_postgresql_connection_string
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.0-flash
CORS_ORIGINS=http://localhost:5174

Start the backend:
uvicorn app.main:app --reload --port 8000

API: http://127.0.0.1:8000
Swagger: http://127.0.0.1:8000/docs

### Frontend

Open a new terminal:

cd frontend
npm install
npm run dev

Open: http://localhost:5174

### Requirements

- PostgreSQL running locally
- Python 3.x
- Node.js + npm
- Gemini API key
