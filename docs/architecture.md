# Tennis Vision — System Architecture

## Overview

Tennis Vision is a full-stack application that accepts a tennis match video, runs it through a multi-model computer vision pipeline, and returns an annotated output video and shot heatmap to the user.

---

## System Diagram

```
┌────────────────────────────────────────────────────────────────────┐
│                                                                    │
│                          USER (Browser)                            │
│                                                                    │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │                    React Frontend                           │  │
│   │   [Upload Video] ──────────────────── [View Results]        │  │
│   │         │              polling               ▲              │  │
│   └─────────┼──────────────────────────────────  ┼  ───────────┘   │
└─────────────┼────────────────────────────────────┼─────────────────┘
              │ POST /upload                        │ GET /download/video
              │                                     │ GET /download/heatmap
              ▼                                     │
┌─────────────────────────────────────────────────────────────────────┐
│                       FastAPI Backend                               │
│                                                                     │
│   /upload ──▶ save file ──▶ assign job_id ──▶ spawn worker process │
│   /status/{job_id}  ◀──── queued / processing / done / failed       │
│   /download/video   ──▶ serve .avi when done                        │
│   /download/heatmap ──▶ serve .png when done                        │
│                                                                     │
└───────────────────────────┬─────────────────────────────────────────┘
                            │ multiprocessing.Process
                            │ calls main() from main.py
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      ML Pipeline (main.py)                          │
│                                                                     │
│   Input Video                                                       │
│       │                                                             │
│       ├──▶ ┌─────────────────────────────┐                         │
│       │    │  YOLOv8x  (pretrained)       │  person detection       │
│       │    │  PlayerTracker               │  + ID tracking          │
│       │    └──────────────┬──────────────┘                          │
│       │                   │ 2 player bboxes / frame                 │
│       │                   ▼                                         │
│       ├──▶ ┌─────────────────────────────┐                          │
│       │    │  YOLOv5  (custom-trained)    │  tennis ball            │
│       │    │  BallTracker                 │  detection              │
│       │    └──────────────┬──────────────┘                          │
│       │                   │ ball bbox / frame + interpolation       │
│       │                   ▼                                         │
│       └──▶ ┌─────────────────────────────┐                         │
│            │  Custom Keypoint CNN         │  court line             │
│            │  CourtLineDetector           │  keypoint regression    │
│            └──────────────┬──────────────┘                          │
│                           │ 28 (x,y) court keypoints                │
│                           ▼                                         │
│            ┌─────────────────────────────┐                          │
│            │  Geometry + Stats Engine     │  mini-court projection  │
│            │  MiniCourt + pandas          │  shot detection         │
│            └──────────────┬──────────────┘  speed calculation       │
│                           │                                         │
│                           ▼                                         │
│            ┌─────────────────────────────┐                          │
│            │  OpenCV Renderer             │  draws bboxes, stats,   │
│            │                              │  mini-court overlay     │
│            └──────────────┬──────────────┘                          │
│                           │                                         │
│              ┌────────────┴────────────┐                            │
│              ▼                         ▼                            │
│        annotated .mp4            shot heatmap .png                  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Components

### Frontend (React + Vite)

- Lets the user upload a video file
- Polls `GET /status/{job_id}` every few seconds while the job runs, showing progress messages
- Displays the annotated video and heatmap image once complete

### Backend (FastAPI)

- `POST /upload` — saves the video, creates a job, spawns a worker process
- `GET /status/{job_id}` — returns job state and current progress message
- `GET /download/video/{job_id}` — serves the output `.avi`
- `GET /download/heatmap/{job_id}` — serves the heatmap `.png`
- `JobManager` uses `multiprocessing` so inference doesn't block the server
- Serves the compiled React build at `/`

### ML Pipeline (`main.py`)

Importable as a library (`from main import main`) and also runnable directly (`python main.py`).

| Step             | Model                     | Purpose                                                                                           |
| ---------------- | ------------------------- | ------------------------------------------------------------------------------------------------- |
| Player detection | YOLOv8x (pretrained COCO) | Detect and track people, filter to the 2 closest to the court                                     |
| Ball detection   | YOLOv5 (custom-trained)   | Detect tennis ball; missing frames filled via pandas interpolation                                |
| Court detection  | Custom keypoint CNN       | Regress 28 court line intersection coordinates from the first frame                               |
| Projection       | Geometry math             | Map real pixel positions onto a top-down mini-court diagram                                       |
| Stats            | pandas                    | Detect shot moments (y-direction reversals), compute ball speed and player movement speed in km/h |
| Rendering        | OpenCV                    | Draw all annotations onto every frame; save video and heatmap                                     |

Detection results are cached as `.pkl` files in `tracker_stubs/` to skip re-inference on reruns.

---

## Data Flow Summary

```
video file
  → player bboxes (per frame)
  → ball bbox (per frame, interpolated)
  → court keypoints (once, from frame 0)
  → mini-court coordinates (player + ball positions projected)
  → shot frames (direction-reversal detection)
  → per-frame stats dataframe (shot count, avg speed, player speed)
  → annotated video frames
  → output .mp4 + heatmap .png
```
