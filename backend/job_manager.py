import multiprocessing
import os
import traceback
import sys
from main import main


def _run_job(jobs, lock, job_id):
    sys.stdout = open("/tmp/worker.log", "w", buffering=1)
    sys.stderr = sys.stdout

    job = dict(jobs[job_id])

    if job.get("use_cpu"):
        # Stubs exist — hide all GPUs so PyTorch/CUDA is never initialized
        os.environ["CUDA_VISIBLE_DEVICES"] = ""

    def _update(**kwargs):
        with lock:
            j = dict(jobs[job_id])
            j.update(kwargs)
            jobs[job_id] = j

    _update(status="processing", progress="Starting...")

    def progress_callback(msg: str):
        _update(progress=msg)

    try:
        main(
            input_video_path=job["input_path"],
            output_video_path=job["output_video_path"],
            heatmap_output_path=job["heatmap_path"],
            progress_callback=progress_callback,
        )
        _update(status="done", progress="Complete")
    except Exception as e:
        traceback.print_exc()
        _update(status="failed", progress="Failed", error=str(e))


class JobManager:
    def __init__(self):
        self._manager = multiprocessing.Manager()
        self._jobs = self._manager.dict()
        self._lock = self._manager.Lock()

    def create_job(self, job_id: str, input_path: str, output_video_path: str, heatmap_path: str, use_cpu: bool = False):
        with self._lock:
            self._jobs[job_id] = {
                "status": "queued",
                "progress": "Queued",
                "input_path": input_path,
                "output_video_path": output_video_path,
                "heatmap_path": heatmap_path,
                "use_cpu": use_cpu,
                "error": None,
            }
        process = multiprocessing.Process(target=_run_job, args=(self._jobs, self._lock, job_id), daemon=True)
        process.start()
        process.join(timeout=0)  # don't block, just register

    def get_job(self, job_id: str) -> dict | None:
        with self._lock:
            job = self._jobs.get(job_id)
            return dict(job) if job is not None else None
