from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.database import engine, Base
from .models.user import User
from .models.patient import Patient
from .models.audit_log import AuditLog
from .models.assessment_history import AssessmentHistory
from .models.subscription import Subscription
from .models.plan_config import PlanConfig
from .api.routes import patients, auth, admin, history, payments, subscriptions, predict

# Create tables in the CareEquity database if they don't exist
Base.metadata.create_all(bind=engine)

# Auto-migration helper for existing tables
try:
    with engine.connect() as conn:
        from sqlalchemy import text
        conn.execute(text("ALTER TABLE assessment_history ADD COLUMN IF NOT EXISTS is_favorite BOOLEAN DEFAULT FALSE;"))
        conn.execute(text("ALTER TABLE patients ADD COLUMN IF NOT EXISTS height_cm FLOAT DEFAULT 170.0;"))
        conn.execute(text("ALTER TABLE patients ADD COLUMN IF NOT EXISTS weight_kg FLOAT DEFAULT 70.0;"))
        conn.commit()
except Exception as migration_err:
    print("Auto migration note:", migration_err)

app = FastAPI(
    title="CareEquity Backend API",
    description="FastAPI service for CareEquity SDOH Integration Platform",
    version="1.0.0"
)

# Configure CORS so the frontend can connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers
app.include_router(patients.router, prefix="/api")
app.include_router(patients.router)
app.include_router(auth.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(history.router, prefix="/api")
app.include_router(payments.router, prefix="/api")
app.include_router(subscriptions.router, prefix="/api")
app.include_router(predict.router)
app.include_router(predict.router, prefix="/api")

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "CareEquity Backend API",
        "database": "Connected"
    }

@app.get("/health")
def health_check():
    return {"status": "ok"}
