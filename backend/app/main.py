from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import auth, instruments, tests, reports, verify, dashboard, history, rules
from app.db.database import engine

app = FastAPI(title="MetraSure API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
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
