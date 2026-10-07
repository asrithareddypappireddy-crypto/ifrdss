"""
main.py
-------
FastAPI backend for IFRDSS (Intelligent Flood Rescue Decision Support System).

Implements the REST API behind the web dashboard described in the SRS:
  POST /api/submissions        -> upload + analyze an image (FR-1.x, FR-2.x, FR-3.x)
  GET  /api/submissions        -> list history, sortable (FR-4.4, FR-4.5)
  GET  /api/submissions/{id}   -> single submission detail
  GET  /uploads/{filename}     -> original uploaded image
  GET  /annotated/{filename}   -> annotated (detections drawn) image

Run with:
    uvicorn main:app --reload --port 8000
(from inside the backend/ directory)
"""

import os
import uuid
import cv2
import numpy as np
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

import detection
import decision_support
import database

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
ANNOTATED_DIR = os.path.join(BASE_DIR, "annotated")
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(ANNOTATED_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}
MAX_FILE_SIZE_MB = 10

app = FastAPI(
    title="IFRDSS API",
    description="Intelligent Flood Rescue Decision Support System backend",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    database.init_db()


@app.post("/api/submissions")
async def create_submission(file: UploadFile = File(...)):
    # ---- FR-1.2 / FR-1.3: validate file type & size ----
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {sorted(ALLOWED_EXTENSIONS)}",
        )

    contents = await file.read()
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({size_mb:.1f} MB). Max allowed is {MAX_FILE_SIZE_MB} MB.",
        )

    # ---- FR-1.4: store with unique identifier ----
    unique_id = uuid.uuid4().hex[:12]
    stored_filename = f"{unique_id}{ext}"
    stored_path = os.path.join(UPLOAD_DIR, stored_filename)
    with open(stored_path, "wb") as f:
        f.write(contents)

    # decode image for OpenCV processing
    file_bytes = np.frombuffer(contents, np.uint8)
    image_bgr = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    if image_bgr is None:
        raise HTTPException(status_code=400, detail="Could not decode image file.")

    # ---- FR-2.1 - FR-2.6: run CV detection pipeline ----
    result = detection.run_detection_pipeline(image_bgr)

    annotated_filename = f"annotated_{stored_filename}"
    annotated_path = os.path.join(ANNOTATED_DIR, annotated_filename)
    cv2.imwrite(annotated_path, result["annotated_image"])

    # ---- FR-3.1 - FR-3.4: decision support ----
    decision = decision_support.evaluate(
        flood_ratio=result["flood_ratio"],
        person_count=result["person_count"],
        damage_score=result["damage_score"],
        damage_flag=result["damage_flag"],
    )

    record = {
        "filename": stored_filename,
        "annotated_filename": annotated_filename,
        "person_count": result["person_count"],
        "flood_ratio": result["flood_ratio"],
        "damage_score": result["damage_score"],
        "damage_flag": result["damage_flag"],
        "rescue_priority": decision["rescue_priority"],
        "risk_level": decision["risk_level"],
        "suggested_response": decision["suggested_response"],
        "rescue_plan": decision["rescue_plan"],
    }
    submission_id = database.insert_submission(record)
    record["id"] = submission_id

    return JSONResponse(content=record)


@app.get("/api/submissions")
def list_submissions(sort_by: str = Query("timestamp"), order: str = Query("desc")):
    return database.get_all_submissions(sort_by=sort_by, order=order)


@app.get("/api/submissions/{submission_id}")
def get_submission(submission_id: int):
    record = database.get_submission(submission_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Submission not found.")
    record["rescue_plan"] = decision_support.generate_actionable_rescue_plan(
        flood_ratio=record["flood_ratio"],
        person_count=record["person_count"],
        damage_score=record["damage_score"],
        damage_flag=bool(record["damage_flag"]),
        risk_level=record["risk_level"],
        priority_score=record["rescue_priority"],
    )
    return record


# ---- Static file mounts ----
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
app.mount("/annotated", StaticFiles(directory=ANNOTATED_DIR), name="annotated")
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
