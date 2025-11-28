# tests/test_api.py

import os
import sys
import csv
import tempfile
import atexit

# Make project root importable
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# ----------------------------
# Temporary CSV setup
# ----------------------------
tmp_csv = tempfile.NamedTemporaryFile(delete=False, mode="w", newline="", encoding="utf-8")
tmp_csv.close()  # close so Flask can open in append mode
CSV_FILE_PATH = tmp_csv.name

# Clean up temp file at exit
def cleanup_temp_csv():
    try:
        os.remove(CSV_FILE_PATH)
    except FileNotFoundError:
        pass

atexit.register(cleanup_temp_csv)

# ----------------------------
# Import Flask app AFTER setting CSV_FILE
# ----------------------------
from app import app, FIELDNAMES

# Patch CSV_FILE in the app module directly
import app as app_module
app_module.CSV_FILE = CSV_FILE_PATH

# ----------------------------
# Helper
# ----------------------------
def client():
    app.testing = True
    return app.test_client()

# Ensure headers are written if file is empty
def ensure_csv_headers():
    if not os.path.exists(CSV_FILE_PATH) or os.path.getsize(CSV_FILE_PATH) == 0:
        with open(CSV_FILE_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()

# ----------------------------
# Tests
# ----------------------------

def test_requires_json():
    ensure_csv_headers()
    c = client()
    r = c.post("/v1/reading_log", data="hi", headers={"Content-Type": "text/plain"})
    assert r.status_code == 400
    assert "invalid_payload" in r.json["error"]

def test_happy_path():
    ensure_csv_headers()
    c = client()

    payload = {
        "name": "Kate",
        "grade": "5",
        "minutes": 20,
        "pages": 10,
        "comments": "Great book!",
        "truth": "yes"
    }

    r = c.post("/v1/reading_log", json=payload)
    assert r.status_code == 200
    assert r.json["status"] == "ok"
    assert r.json["saved"] is True

    # Verify CSV written
    with open(CSV_FILE_PATH, newline="") as f:
        rows = list(csv.DictReader(f))
        # Only one row should exist
        assert len(rows) == 1
        assert rows[0]["name"] == "Kate"
        assert rows[0]["grade"] == "5"

def test_dashboard_data_returns_valid_json():
    ensure_csv_headers()
    # Seed CSV with one entry
    with open(CSV_FILE_PATH, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(FIELDNAMES)
        writer.writerow(["11/10", "10:00", "Sam", "3", "15", "12", "", "yes"])

    c = client()
    r = c.get("/v1/dashboard_data")
    assert r.status_code == 200
    data = r.json

    expected_keys = [
        "recent",
        "all_grades",
        "pages_chart",
        "minutes_chart",
        "leaderboard",
        "leaderboard2",
        "pages_by_grade",
        "minutes_by_grade",
        "overall_total_pages",
        "overall_total_minutes"
    ]
    for key in expected_keys:
        assert key in data

def test_root_smoke():
    c = client()
    r = c.get("/")
    assert r.status_code == 200
    assert "message" in r.json

def test_form_route():
    c = client()
    r = c.get("/form")
    assert r.status_code == 200
    assert b"<" in r.data  # crude check for HTML content

def test_download_csv():
    ensure_csv_headers()
    c = client()
    r = c.get("/download_csv")
    assert r.status_code == 200
    assert r.headers["Content-Disposition"].startswith("attachment")
