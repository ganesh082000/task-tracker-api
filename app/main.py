# main.py
import os
import time
import logging
from datetime import date

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv

# Prometheus
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

# --- Load environment variables ---
load_dotenv()

# --- Logging configuration ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("task_api")

# --- Database configuration ---
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_NAME = os.getenv("POSTGRES_DB")
DB_HOST = os.getenv("POSTGRES_HOST")
DB_PORT = os.getenv("POSTGRES_PORT")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

class TaskDB(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    start_date = Column(Date)
    end_date = Column(Date)
    completed = Column(Boolean, default=False)

Base.metadata.create_all(bind=engine)

# --- FastAPI app ---
app = FastAPI(title="Task Tracker API")

# --- Prometheus metrics ---
REQUEST_COUNT = Counter(
    "task_api_requests_total", "Total number of requests", ["endpoint", "method"]
)
REQUEST_LATENCY = Histogram(
    "task_api_request_latency_seconds", "Request latency in seconds", ["endpoint"]
)

# --- Middleware for metrics ---
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    resp_time = time.time() - start

    REQUEST_COUNT.labels(endpoint=request.url.path, method=request.method).inc()
    REQUEST_LATENCY.labels(endpoint=request.url.path).observe(resp_time)

    logger.info(f"{request.method} {request.url.path} completed in {resp_time:.4f}s")
    return response

# --- Prometheus metrics endpoint ---
@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# --- Pydantic schema ---
class Task(BaseModel):
    title: str
    start_date: date
    end_date: date | None = None
    completed: bool = False

# --- Dependency for DB session ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Endpoints ---
@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/tasks", response_model=Task)
def create_task(task: Task, db: Session = Depends(get_db)):
    try:
        new_task = TaskDB(**task.dict())
        db.add(new_task)
        db.commit()
        db.refresh(new_task)
        logger.info(f"Task created with id={new_task.id}")
        return new_task
    except Exception as e:
        logger.error(f"Failed to create task: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/tasks")
def get_tasks(db: Session = Depends(get_db)):
    try:
        tasks = db.query(TaskDB).all()
        logger.info(f"Retrieved {len(tasks)} tasks")
        return tasks
    except Exception as e:
        logger.error(f"Failed to retrieve tasks: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
