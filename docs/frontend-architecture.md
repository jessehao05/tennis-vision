# Frontend Architecture Plan

## Overview

A local web UI to replace the current workflow of manually editing hardcoded paths in `main.py`.
All processing runs on the GPU cluster. The UI is accessed from a local browser via SSH port forwarding.

---

## Current Workflow (to replace)

1. Drop video into `input_videos/`
2. Manually edit input/output path variables in `main.py`
3. Run `python main.py` in terminal
4. Find output video in `output_videos/` and heatmap in `output_visuals/`

---

## Target Architecture

```
[local browser :8080] <-- SSH tunnel --> [FastAPI on cluster :8080]
                                              |
                                              ├── serves React build (static files)
                                              ├── manages background jobs (in-memory)
                                              └── runs main.py pipeline in background thread
```

Single port, single SSH tunnel, one process to start on the cluster.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/upload` | Accept video file, save to `input_videos/`, start background job, return `job_id` |
| `GET` | `/status/{job_id}` | Return `{ status, progress_message }` |
| `GET` | `/download/video/{job_id}` | Stream output `.avi` |
| `GET` | `/download/heatmap/{job_id}` | Stream heatmap image |

---

## Job Lifecycle

```
upload --> queued --> processing --> done
                          |
                          └--> failed
```

- Each job gets a UUID tied to its input/output file paths
- Job state lives in an in-memory dict (no database needed)
- Pipeline runs in a background thread, calling a refactored `main()`

---

## Frontend (React)

Three views, no routing needed:

1. **Upload** — drag/drop or file picker, POST to `/upload`
2. **Processing** — polls `/status/{job_id}` every 2 seconds, displays current pipeline step
3. **Results** — video player + heatmap image, with download buttons

---

## File Structure

```
tennis-vision/
├── main.py                  # refactor: accept input/output paths as params
├── backend/
│   ├── app.py               # FastAPI app
│   └── job_manager.py       # in-memory job state
├── frontend/
│   ├── src/
│   └── package.json
└── docs/
    └── frontend-architecture.md
```

---

## Required Refactor to `main.py`

`main()` currently hardcodes all paths. It needs to accept parameters so the backend can invoke it per-job:

```python
def main(input_video_path: str, output_video_path: str, heatmap_output_path: str):
    ...
```

---

## Usage Once Built

```bash
# On the cluster (once)
cd tennis-vision && uvicorn backend.app:app --host 0.0.0.0 --port 8080

# On your laptop (once per session)
ssh -L 8080:localhost:8080 user@cluster

# Then open in browser
localhost:8080
```

---

## Implementation Order

1. Refactor `main.py` to accept path params
2. Build FastAPI backend + job manager
3. Build React frontend
4. Wire SSH tunnel and test end to end
