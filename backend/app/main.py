from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import auth, instruments, tests, reports, verify, dashboard, history, rules
from app.core.config import settings
from app.db.database import engine, SessionLocal
from app.db.models import Base, User

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ephemeral hosts (e.g. Render free tier) start with an empty DB: create tables and seed demo data
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        needs_seed = db.query(User).count() == 0
    finally:
        db.close()
    if needs_seed:
        from seed import seed_demo_data
        seed_demo_data()
    yield

app = FastAPI(title="MetraSure API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(instruments.router, prefix="/api")
app.include_router(tests.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(verify.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(history.router, prefix="/api")
app.include_router(rules.router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Welcome to MetraSure API"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
