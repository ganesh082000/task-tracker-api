# main.py
from fastapi import FastAPI
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import date
from dotenv import load_dotenv
import os
import time

# Prometheus
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

# Load .env
load_dotenv()

# --- Database configuration ---
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_NAME = os.getenv("POSTGRES_DB")
DB_HOST = os.getenv("POSTGRES_HOST")
DB_PORT = os.getenv("POSTGRES_PORT")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
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

@app.middleware("http")
async def metrics_middleware(request, call_next):
    start = time.time()
    response = await call_next(request)
    resp_time = time.time() - start

    REQUEST_COUNT.labels(endpoint=request.url.path, method=request.method).inc()
    REQUEST_LATENCY.labels(endpoint=request.url.path).observe(resp_time)
    return response

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# --- Pydantic schema ---
class Task(BaseModel):
    title: str
    start_date: date
    end_date: date | None = None
    completed: bool = False

# --- Endpoints ---
@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/tasks")
def create_task(task: Task):
    db = SessionLocal()
    new_task = TaskDB(**task.dict())
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    db.close()
    return new_task

@app.get("/tasks")
def get_tasks():
    db = SessionLocal()
    tasks = db.query(TaskDB).all()
    db.close()
    return tasks
