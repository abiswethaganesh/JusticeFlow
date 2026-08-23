import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.config import settings
from app.database import engine, Base, SessionLocal
from app.models import (  # noqa: F401
    user,
    police_station,
    officer,
    complaint,
    case_evidence,
    case_event,
    fir_record,
)
from app.routers import auth, intake, complaints, evidence, forms
from app.services.auth_service import seed_default_users_if_needed

app = FastAPI(title="JusticeFlow Core Platform API")

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Upload directory static mounting
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Include Routers
app.include_router(auth.router)
app.include_router(intake.router)
app.include_router(complaints.router)
app.include_router(evidence.router)
app.include_router(forms.router)


@app.on_event("startup")
def on_startup():
    # Create all database tables
    Base.metadata.create_all(bind=engine)

    # Safely alter existing users and complaints tables if columns are missing
    try:
        inspector = inspect(engine)
        if "users" in inspector.get_table_names():
            user_cols = [c["name"] for c in inspector.get_columns("users")]
            with engine.begin() as conn:
                if "email" not in user_cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN email VARCHAR(100) DEFAULT '' NOT NULL"))
                if "password_hash" not in user_cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN password_hash VARCHAR(255) DEFAULT '' NOT NULL"))
                if "is_active" not in user_cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT TRUE NOT NULL"))

        if "complaints" in inspector.get_table_names():
            comp_cols = [c["name"] for c in inspector.get_columns("complaints")]
            with engine.begin() as conn:
                if "citizen_id" not in comp_cols:
                    conn.execute(text("ALTER TABLE complaints ADD COLUMN citizen_id INTEGER NULL"))
                if "police_station_id" not in comp_cols:
                    conn.execute(text("ALTER TABLE complaints ADD COLUMN police_station_id INTEGER NULL"))
                if "workflow_type" not in comp_cols:
                    conn.execute(text("ALTER TABLE complaints ADD COLUMN workflow_type VARCHAR(50) DEFAULT 'cognizable_fir' NOT NULL"))
                if "original_complaint" not in comp_cols:
                    conn.execute(text("ALTER TABLE complaints ADD COLUMN original_complaint TEXT DEFAULT '' NOT NULL"))
                if "incident_details" not in comp_cols:
                    conn.execute(text("ALTER TABLE complaints ADD COLUMN incident_details JSON DEFAULT '{}' NOT NULL"))
                if "priority" not in comp_cols:
                    conn.execute(text("ALTER TABLE complaints ADD COLUMN priority VARCHAR(20) DEFAULT 'MEDIUM' NOT NULL"))
                if "is_cognizable" not in comp_cols:
                    conn.execute(text("ALTER TABLE complaints ADD COLUMN is_cognizable BOOLEAN DEFAULT TRUE NOT NULL"))
                if "updated_at" not in comp_cols:
                    conn.execute(text("ALTER TABLE complaints ADD COLUMN updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL"))
    except Exception as e:
        print(f"[DB Schema Note] Column alteration: {e}")

    # Seed default police stations and test officer accounts
    db: Session = SessionLocal()
    try:
        seed_default_users_if_needed(db)
    except Exception as e:
        print(f"[DB Startup Note] Database seeding: {e}")
    finally:
        db.close()


@app.get("/health")
def health():
    return {"status": "ok", "platform": "JusticeFlow Core Platform Engine"}
