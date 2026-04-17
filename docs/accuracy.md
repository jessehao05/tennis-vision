# Model Accuracy Metrics

This document outlines the metrics used to evaluate the accuracy of the tennis ball tracking model. The model takes a video as input and outputs a video with bounding box markers drawn on the detected ball.

---

## Detection Metrics (per frame)

### Precision / Recall / F1

- **Precision**: Of all frames where the model drew a bounding box, how many actually contained a ball? High precision means few false positives.
- **Recall**: Of all frames where a ball was present, how many did the model detect? High recall means few missed detections.
- **F1 Score**: The harmonic mean of precision and recall. Use this as the primary headline number when comparing model versions.

### mAP (Mean Average Precision)

The standard YOLO evaluation metric, built into `ultralytics`. Run `model.val()` to get this automatically.

- **mAP@50**: Measures detection quality at an IoU threshold of 0.5 — the predicted box must overlap the ground-truth box by at least 50%.
- **mAP@50-95**: Averages mAP across IoU thresholds from 0.5 to 0.95 in 0.05 steps. A stricter, more comprehensive measure.

---

## Localization Metrics

### IoU (Intersection over Union)

Measures how much the predicted bounding box overlaps with the ground-truth box, on a scale from 0 to 1.

```
IoU = Area of Overlap / Area of Union
```

The current model uses a low confidence threshold (`conf=0.15` in `ball_tracker.py`), which favors recall over precision and may lower average IoU.

### Center Distance Error

Euclidean distance in pixels between the center of the predicted bounding box and the center of the ground-truth box. More interpretable than IoU for a small, fast-moving object like a tennis ball.

```
center_distance = sqrt((x_pred - x_gt)^2 + (y_pred - y_gt)^2)
```

Report as mean and 90th-percentile across all detected frames.

---

## Tracking / Temporal Metrics

### Miss Rate per Rally

The number of consecutive frames where the ball goes undetected before interpolation fills in the gap (`interpolate_ball_positions` in `ball_tracker.py`). A high miss rate means the output trajectory is heavily interpolated rather than directly observed.

### Hit Detection Accuracy

The `get_ball_shot_frames` method in `ball_tracker.py` detects frames where the ball was hit based on directional changes in the ball's y-position. Compare detected hit frames against manually labeled ground-truth hit frames:

- **Precision**: Of detected hits, how many were real?
- **Recall**: Of real hits, how many were detected?
- **Frame offset error**: How many frames off is the detected hit from the true hit frame?

---

## How to Evaluate

The fastest path to getting these numbers:

1. Label 200–500 frames with ground-truth bounding boxes (e.g., using [Roboflow](https://roboflow.com) or [CVAT](https://cvat.ai)).
2. Run `model.val()` from `ultralytics` — this returns mAP, precision, recall, and a confusion matrix automatically.
3. For center distance error and hit detection accuracy, write a small evaluation script that compares model output against your labeled frames.
