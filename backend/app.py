import csv
import os
import shutil
import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from backend.job_manager import JobManager

app = FastAPI()
manager = JobManager()


def _stubs_exist(video_name: str) -> bool:
    player_stub = f"tracker_stubs/{video_name}_player_detections.pkl"
    ball_stub = f"tracker_stubs/{video_name}_ball_detections.pkl"
    return os.path.exists(player_stub) and os.path.exists(ball_stub)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    job_id = str(uuid.uuid4())
    original_name = os.path.splitext(file.filename)[0]

    input_path = f"input_videos/{file.filename}"
    output_video_path = f"output_videos/{original_name}.mp4"
    heatmap_path = f"output_visuals/{original_name}.png"

    with open(input_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    use_cpu = _stubs_exist(original_name)

    manager.create_job(
        job_id=job_id,
        input_path=input_path,
        output_video_path=output_video_path,
        heatmap_path=heatmap_path,
        video_name=original_name,
        use_cpu=use_cpu,
    )

    return {"job_id": job_id}


@app.get("/status/{job_id}")
def status(job_id: str):
    job = manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"status": job["status"], "progress": job["progress"], "error": job["error"]}


@app.get("/download/video/{job_id}")
def download_video(job_id: str):
    job = manager.get_job(job_id)
    if not job or job["status"] != "done":
        raise HTTPException(status_code=404, detail="Not ready")
    return FileResponse(job["output_video_path"], media_type="video/mp4", filename=f"{job_id}.mp4")


@app.get("/download/heatmap/{job_id}")
def download_heatmap(job_id: str):
    job = manager.get_job(job_id)
    if not job or job["status"] != "done":
        raise HTTPException(status_code=404, detail="Not ready")
    return FileResponse(job["heatmap_path"], media_type="image/png", filename=f"{job_id}.png")


@app.get("/stats/{job_id}")
def get_stats(job_id: str):
    job = manager.get_job(job_id)
    if not job or job["status"] != "done":
        raise HTTPException(status_code=404, detail="Not ready")
    video_name = job.get("video_name", "")

    def read_csv(path):
        if not os.path.exists(path):
            return []
        with open(path, newline="") as f:
            return list(csv.DictReader(f))

    per_shot = read_csv(f"output_csv/{video_name}_per_shot_stats.csv")
    accuracy = _compute_accuracy(per_shot)

    return {
        "summary": read_csv(f"output_csv/{video_name}_match_summary.csv"),
        "per_shot": per_shot,
        "accuracy": accuracy,
    }


def _compute_accuracy(per_shot: list) -> dict:
    if not per_shot:
        return {}

    ball_speeds = []
    p1_speeds = []
    p2_speeds = []
    rally_lengths: dict[str, int] = {}

    for row in per_shot:
        try:
            ball_speeds.append(float(row["ball_speed_kmh"]))
        except (ValueError, KeyError):
            pass
        try:
            p1_speeds.append(float(row["player_1_speed_kmh"]))
        except (ValueError, KeyError):
            pass
        try:
            p2_speeds.append(float(row["player_2_speed_kmh"]))
        except (ValueError, KeyError):
            pass
        rally = row.get("rally_number", "0")
        rally_lengths[rally] = rally_lengths.get(rally, 0) + 1

    BALL_SPEED_LOW  = 10    # km/h — below this is almost certainly a tracking error
    BALL_SPEED_HIGH = 250   # km/h — above this is physically implausible
    PLAYER_SPEED_MAX = 35   # km/h — fastest recorded sprint on court

    n = len(ball_speeds)
    ball_outliers = [s for s in ball_speeds if s < BALL_SPEED_LOW or s > BALL_SPEED_HIGH]
    p1_flags = [s for s in p1_speeds if s > PLAYER_SPEED_MAX]
    p2_flags = [s for s in p2_speeds if s > PLAYER_SPEED_MAX]
    valid_shots = n - len(ball_outliers)
    tracking_quality = round(valid_shots / n * 100, 1) if n else 0

    lengths = list(rally_lengths.values())

    def safe_round(val, digits=1):
        return round(val, digits) if val is not None else None

    return {
        "total_shots": len(per_shot),
        "tracking_quality_pct": tracking_quality,
        "ball_speed": {
            "mean":     safe_round(sum(ball_speeds) / n) if n else None,
            "min":      safe_round(min(ball_speeds))     if ball_speeds else None,
            "max":      safe_round(max(ball_speeds))     if ball_speeds else None,
            "outliers": len(ball_outliers),
            "threshold_low":  BALL_SPEED_LOW,
            "threshold_high": BALL_SPEED_HIGH,
        },
        "player_speed": {
            "p1_flagged":  len(p1_flags),
            "p2_flagged":  len(p2_flags),
            "threshold":   PLAYER_SPEED_MAX,
        },
        "rally": {
            "total":      len(lengths),
            "avg_length": safe_round(sum(lengths) / len(lengths)) if lengths else None,
            "longest":    max(lengths) if lengths else None,
            "shortest":   min(lengths) if lengths else None,
        },
    }


@app.get("/download/csv/summary/{job_id}")
def download_csv_summary(job_id: str):
    job = manager.get_job(job_id)
    if not job or job["status"] != "done":
        raise HTTPException(status_code=404, detail="Not ready")
    path = f"output_csv/{job.get('video_name', '')}_match_summary.csv"
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="CSV not found")
    return FileResponse(path, media_type="text/csv", filename="match_summary.csv")


@app.get("/download/csv/per-shot/{job_id}")
def download_csv_per_shot(job_id: str):
    job = manager.get_job(job_id)
    if not job or job["status"] != "done":
        raise HTTPException(status_code=404, detail="Not ready")
    path = f"output_csv/{job.get('video_name', '')}_per_shot_stats.csv"
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="CSV not found")
    return FileResponse(path, media_type="text/csv", filename="per_shot_stats.csv")


# Serve React build — must be last so it doesn't shadow API routes
frontend_build = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.isdir(frontend_build):
    app.mount("/", StaticFiles(directory=frontend_build, html=True), name="frontend")
