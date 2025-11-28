from flask import Flask, request, jsonify, render_template
import csv
import os
from datetime import datetime
from flask import send_file
from dotenv import load_dotenv

# Load environment variables from a .env file if present
load_dotenv()

# CSV file path from environment or default
CSV_FILE = os.getenv("CSV_FILE", "reading_log.csv")

# Optional: Flask secret key
SECRET_KEY = os.getenv("SECRET_KEY", "change-me")

# Optional: host and port
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 5000))

app = Flask(__name__, template_folder="frontend", static_folder="frontend")

FIELDNAMES = ["date", "time", "name", "grade", "minutes", "pages", "comments", "truth"]

# Serve the HTML form
@app.route("/form")
def form():
    return render_template("index.html")

# API endpoint to collect reading log submissions
@app.route("/v1/reading_log", methods=["POST"])
def collect_reading_log():
    try:
        data = request.get_json(force=True)
        row = {
            "date": datetime.now().strftime("%m/%d"),
            "time": datetime.now().strftime("%H:%M"),
            "name": data.get("name", ""),
            "grade": data.get("grade", ""),
            "minutes": data.get("minutes", ""),
            "pages": data.get("pages", ""),
            "comments": data.get("comments", ""),
            "truth": data.get("truth", ""),
        }

        file_exists = os.path.exists(CSV_FILE)
        with open(CSV_FILE, "a", newline='', encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)

        return jsonify({"status": "ok", "saved": True}), 200

    except Exception as e:
        return jsonify({"error": "invalid_payload", "detail": str(e)}), 400

# Optional: test endpoint
@app.route("/")
def home():
    return jsonify({"message": "Flask CSV API is running"})

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/v1/dashboard_data")
def dashboard_data():
    import csv
    from datetime import datetime, timedelta
    from collections import defaultdict

    rows = []
    all_grades = set()

    # Load CSV
    try:
        with open(CSV_FILE, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                row["pages"] = int(row.get("pages", 0) or 0)
                row["minutes"] = int(row.get("minutes", 0) or 0)
                row["grade"] = row.get("grade", "") or ""
                row["date"] = (row.get("date", "") or "").strip()
                row["time"] = (row.get("time", "") or "").strip()
                row["name"] = row.get("name", "") or ""
                rows.append(row)
                if row["grade"]:
                    all_grades.add(row["grade"])
    except FileNotFoundError:
        pass

    # Most recent 10 submissions
    recent = sorted(
        rows,
        key=lambda r: (r.get("date") or "") + (r.get("time") or ""),
        reverse=True
    )[:10]

    # Last 14 days
    two_weeks_ago = datetime.now() - timedelta(days=7)
    daily_pages = defaultdict(int)
    daily_minutes = defaultdict(int)

    # Grade-specific
    daily_pages_by_grade = defaultdict(lambda: defaultdict(int))
    daily_minutes_by_grade = defaultdict(lambda: defaultdict(int))

    current_year = datetime.now().year

    for row in rows:
        date_str = row["date"]
        time_str = row["time"]
        grade = row["grade"]

        if not date_str or not time_str:
            continue

        try:
            ts = datetime.strptime(f"{current_year}/{date_str} {time_str}", "%Y/%m/%d %H:%M")
            if ts >= two_weeks_ago:
                d = ts.date()

                # global totals
                daily_pages[d] += row["pages"]
                daily_minutes[d] += row["minutes"]

                # grade-specific totals
                if grade:
                    daily_pages_by_grade[grade][d] += row["pages"]
                    daily_minutes_by_grade[grade][d] += row["minutes"]

        except:
            continue

    # Sort dates
    dates_sorted = sorted(daily_pages.keys())

    # Base charts
    pages_chart = {
        "labels": [d.strftime("%m/%d") for d in dates_sorted],
        "values": [daily_pages[d] for d in dates_sorted],
        "labels_by_grade": {},
        "values_by_grade": {}
    }

    minutes_chart = {
        "labels": [d.strftime("%m/%d") for d in dates_sorted],
        "values": [daily_minutes[d] for d in dates_sorted],
        "labels_by_grade": {},
        "values_by_grade": {}
    }

    # Fill grade-specific charts
    for g in all_grades:
        grade_dates = sorted(daily_pages_by_grade[g].keys())

        pages_chart["labels_by_grade"][g] = [d.strftime("%m/%d") for d in grade_dates]
        pages_chart["values_by_grade"][g] = [daily_pages_by_grade[g][d] for d in grade_dates]

        minutes_chart["labels_by_grade"][g] = [d.strftime("%m/%d") for d in grade_dates]
        minutes_chart["values_by_grade"][g] = [daily_minutes_by_grade[g][d] for d in grade_dates]

    # Leaderboard 1: pages
    leaderboard_data = defaultdict(int)
    for row in rows:
        leaderboard_data[row["name"]] += row["pages"]

    leaderboard = sorted(
        [{"name": k, "total_pages": v} for k, v in leaderboard_data.items()],
        key=lambda x: x["total_pages"],
        reverse=True
    )[:5]

    # Leaderboard 2: minutes
    leaderboard_data2 = defaultdict(int)
    for row in rows:
        leaderboard_data2[row["name"]] += row["minutes"]

    leaderboard2 = sorted(
        [{"name": k, "total_minutes": v} for k, v in leaderboard_data2.items()],
        key=lambda x: x["total_minutes"],
        reverse=True
    )[:5]

    # Total pages by grade
    pages_by_grade = defaultdict(int)
    overall_total_pages = 0
    for row in rows:
        pages = row["pages"]
        overall_total_pages += pages
        grade = row["grade"]
        if grade:
            pages_by_grade[grade] += pages

    pages_by_grade_list = sorted(
        [{"grade": k, "total_pages": v} for k, v in pages_by_grade.items()],
        key=lambda x: x["grade"]
    )

    # Total minutes by grade
    minutes_by_grade = defaultdict(int)
    overall_total_minutes = 0
    for row in rows:
        minutes = row["minutes"]
        overall_total_minutes += minutes
        grade = row["grade"]
        if grade:
            minutes_by_grade[grade] += minutes

    minutes_by_grade_list = sorted(
        [{"grade": k, "total_minutes": v} for k, v in minutes_by_grade.items()],
        key=lambda x: x["grade"]
    )

    return jsonify({
        "recent": recent,
        "all_grades": list(all_grades),
        "pages_chart": pages_chart,
        "minutes_chart": minutes_chart,
        "leaderboard": leaderboard,
        "leaderboard2": leaderboard2,
        "pages_by_grade": pages_by_grade_list,
        "overall_total_pages": overall_total_pages,
        "minutes_by_grade": minutes_by_grade_list,
        "overall_total_minutes": overall_total_minutes
    })

@app.route("/download_csv")
def download_csv():
    return send_file(CSV_FILE, as_attachment=True)

if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=True)
