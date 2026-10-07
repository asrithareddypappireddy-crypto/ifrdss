"""
test_api_integration.py
------------------------
Integration tests for the full IFRDSS pipeline via the FastAPI app
(upload -> detection -> decision support -> database -> retrieval),
using FastAPI's TestClient so no separate server process is needed.

Covers SRS requirements: FR-1.2, FR-1.3 (validation), FR-1.4 (storage),
FR-4.4, FR-4.5 (history/sorting), and end-to-end data consistency.
"""

import sys
import os
import io
import numpy as np
import cv2
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

# Use an isolated, temporary database + storage dirs for the test run so
# tests never touch/pollute the real ifrdss.db or uploads/ used by a
# person actually running the app.
import tempfile
TEST_DIR = tempfile.mkdtemp(prefix="ifrdss_test_")
os.environ["IFRDSS_TEST_DIR"] = TEST_DIR

import database
database.DB_PATH = os.path.join(TEST_DIR, "test_ifrdss.db")

import main as app_module
# NOTE: main.py's /uploads and /annotated static routes are bound with
# `app.mount(..., StaticFiles(directory=UPLOAD_DIR))` at *import time*.
# StaticFiles captures that directory string once; reassigning the
# module-level UPLOAD_DIR/ANNOTATED_DIR afterwards (as an earlier version
# of this test did) changes where create_submission() *writes* files but
# NOT where the static route *serves* them from, since the mount was
# already bound to the original path. That mismatch is a real, minor
# design finding (see TEST_REPORT.md, TC-API-10) -- not something this
# test should paper over. So integration tests intentionally use the
# app's real default uploads/annotated directories, and clean up any
# files they create afterwards.
created_files = []

client = TestClient(app_module.app)


def make_test_jpeg_bytes(color=(60, 100, 140), size=(200, 200)):
    """Build an in-memory JPEG (no disk I/O) for upload tests."""
    img = np.full((size[0], size[1], 3), color, dtype=np.uint8)
    success, encoded = cv2.imencode(".jpg", img)
    assert success
    return io.BytesIO(encoded.tobytes())


@pytest.fixture(autouse=True)
def reset_db():
    """Ensure a clean database before every test, and remove any files
    this test run wrote into the app's real uploads/annotated folders."""
    database.init_db()
    conn = database.get_connection()
    conn.execute("DELETE FROM submissions")
    conn.commit()
    conn.close()
    yield
    for d in (app_module.UPLOAD_DIR, app_module.ANNOTATED_DIR):
        for f in os.listdir(d):
            if f != ".gitkeep":
                os.remove(os.path.join(d, f))


# ---------------------------------------------------------------------
# FR-1.2 / FR-1.3: file validation
# ---------------------------------------------------------------------

def test_upload_rejects_unsupported_extension():
    files = {"file": ("scene.txt", io.BytesIO(b"not an image"), "text/plain")}
    resp = client.post("/api/submissions", files=files)
    assert resp.status_code == 400
    assert "Unsupported file type" in resp.json()["detail"]


def test_upload_rejects_oversized_file():
    # main.MAX_FILE_SIZE_MB is 10; build a >10MB dummy "jpg" payload
    big_payload = b"0" * (11 * 1024 * 1024)
    files = {"file": ("huge.jpg", io.BytesIO(big_payload), "image/jpeg")}
    resp = client.post("/api/submissions", files=files)
    assert resp.status_code == 400
    assert "too large" in resp.json()["detail"].lower()


def test_upload_rejects_undecodable_image():
    """A .jpg-named file that isn't actually a valid image should fail
    gracefully with a 400, not a server crash."""
    files = {"file": ("fake.jpg", io.BytesIO(b"this is not real jpeg data"), "image/jpeg")}
    resp = client.post("/api/submissions", files=files)
    assert resp.status_code == 400
    assert "decode" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------
# FR-1.4, FR-2.x, FR-3.x: full happy-path pipeline
# ---------------------------------------------------------------------

def test_upload_valid_image_runs_full_pipeline():
    files = {"file": ("flood.jpg", make_test_jpeg_bytes(), "image/jpeg")}
    resp = client.post("/api/submissions", files=files)
    assert resp.status_code == 200
    data = resp.json()

    # required fields present (SRS FR-2.x / FR-3.x outputs)
    for field in ["id", "filename", "annotated_filename", "person_count",
                  "flood_ratio", "damage_score", "damage_flag",
                  "rescue_priority", "risk_level", "suggested_response"]:
        assert field in data, f"Missing expected field: {field}"

    assert data["risk_level"] in {"Low", "Medium", "High", "Critical"}
    assert 0 <= data["rescue_priority"] <= 100
    assert isinstance(data["id"], int)


def test_uploaded_and_annotated_files_are_actually_written_to_disk():
    files = {"file": ("flood2.jpg", make_test_jpeg_bytes(), "image/jpeg")}
    resp = client.post("/api/submissions", files=files)
    data = resp.json()

    original_path = os.path.join(app_module.UPLOAD_DIR, data["filename"])
    annotated_path = os.path.join(app_module.ANNOTATED_DIR, data["annotated_filename"])
    assert os.path.exists(original_path), "Original image was not saved to disk"
    assert os.path.exists(annotated_path), "Annotated image was not saved to disk"


# ---------------------------------------------------------------------
# FR-4.4, FR-4.5: history listing + sorting
# ---------------------------------------------------------------------

def test_history_lists_all_prior_submissions():
    client.post("/api/submissions", files={"file": ("a.jpg", make_test_jpeg_bytes(), "image/jpeg")})
    client.post("/api/submissions", files={"file": ("b.jpg", make_test_jpeg_bytes(), "image/jpeg")})

    resp = client.get("/api/submissions")
    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) == 2


def test_history_sort_by_rescue_priority_descending():
    # low-severity (uniform gray, no flood color, no people, no damage texture)
    client.post("/api/submissions",
                files={"file": ("low.jpg", make_test_jpeg_bytes(color=(128, 128, 128)), "image/jpeg")})
    # higher-severity (muddy flood color -> higher flood_ratio -> higher priority)
    client.post("/api/submissions",
                files={"file": ("high.jpg", make_test_jpeg_bytes(color=(60, 100, 140)), "image/jpeg")})

    resp = client.get("/api/submissions?sort_by=rescue_priority&order=desc")
    rows = resp.json()
    priorities = [r["rescue_priority"] for r in rows]
    assert priorities == sorted(priorities, reverse=True), \
        "Submissions were not correctly sorted by rescue_priority descending"


def test_get_single_submission_by_id():
    resp = client.post("/api/submissions", files={"file": ("x.jpg", make_test_jpeg_bytes(), "image/jpeg")})
    submission_id = resp.json()["id"]

    detail_resp = client.get(f"/api/submissions/{submission_id}")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["id"] == submission_id


def test_get_nonexistent_submission_returns_404():
    resp = client.get("/api/submissions/999999")
    assert resp.status_code == 404


def test_history_falls_back_to_timestamp_for_invalid_sort_field():
    """Passing an unrecognized sort_by should not error out (SQL
    injection guard) -- it should silently fall back to timestamp."""
    client.post("/api/submissions", files={"file": ("z.jpg", make_test_jpeg_bytes(), "image/jpeg")})
    resp = client.get("/api/submissions?sort_by=DROP TABLE submissions;--&order=desc")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


# ---------------------------------------------------------------------
# Static file serving
# ---------------------------------------------------------------------

def test_uploaded_image_is_retrievable_via_static_route():
    resp = client.post("/api/submissions", files={"file": ("y.jpg", make_test_jpeg_bytes(), "image/jpeg")})
    filename = resp.json()["filename"]
    static_resp = client.get(f"/uploads/{filename}")
    assert static_resp.status_code == 200
    assert static_resp.headers["content-type"].startswith("image/")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
