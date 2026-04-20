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


# Serve React build — must be last so it doesn't shadow API routes
frontend_build = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.isdir(frontend_build):
    app.mount("/", StaticFiles(directory=frontend_build, html=True), name="frontend")
