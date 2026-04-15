import threading
from main import main


class JobManager:
    def __init__(self):
        self._jobs: dict = {}
        self._lock = threading.Lock()

    def create_job(self, job_id: str, input_path: str, output_video_path: str, heatmap_path: str):
        with self._lock:
            self._jobs[job_id] = {
                "status": "queued",
                "progress": "Queued",
                "input_path": input_path,
                "output_video_path": output_video_path,
                "heatmap_path": heatmap_path,
                "error": None,
            }
        thread = threading.Thread(target=self._run, args=(job_id,), daemon=True)
        thread.start()

    def get_job(self, job_id: str) -> dict | None:
        with self._lock:
            return self._jobs.get(job_id)

    def _update(self, job_id: str, **kwargs):
        with self._lock:
            self._jobs[job_id].update(kwargs)

    def _run(self, job_id: str):
        job = self._jobs[job_id]
        self._update(job_id, status="processing", progress="Starting...")

        def progress_callback(msg: str):
            self._update(job_id, progress=msg)

        try:
            main(
                input_video_path=job["input_path"],
                output_video_path=job["output_video_path"],
                heatmap_output_path=job["heatmap_path"],
                progress_callback=progress_callback,
            )
            self._update(job_id, status="done", progress="Complete")
        except Exception as e:
            self._update(job_id, status="failed", progress="Failed", error=str(e))
