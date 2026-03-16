"""
GPU benchmark script for tennis vision YOLO inference.

Runs batched inference on repeated frames to stress-test GPU vs CPU throughput.
Useful for testing that a computing cluster has GPU access and measuring speedup.

Usage:
    python misc/gpu_benchmark.py
    python misc/gpu_benchmark.py --model yolov8x --frames 500 --batch-size 8
"""

import argparse
import time
import numpy as np
import torch
from ultralytics import YOLO


def parse_args():
    parser = argparse.ArgumentParser(description="Benchmark YOLO inference on GPU vs CPU")
    parser.add_argument("--model", default="yolov8x", help="YOLO model variant (default: yolov8x)")
    parser.add_argument("--frames", type=int, default=300, help="Number of synthetic frames to run (default: 300)")
    parser.add_argument("--batch-size", type=int, default=4, help="Inference batch size (default: 4)")
    parser.add_argument("--imgsz", type=int, default=640, help="Input image size (default: 640)")
    parser.add_argument("--cpu-only", action="store_true", help="Force CPU even if GPU is available")
    return parser.parse_args()


def make_synthetic_frames(n: int, imgsz: int) -> list[np.ndarray]:
    """Generate random uint8 frames that look like video frames to the model."""
    rng = np.random.default_rng(42)
    return [rng.integers(0, 256, (imgsz, imgsz, 3), dtype=np.uint8) for _ in range(n)]


def run_benchmark(model: YOLO, frames: list[np.ndarray], batch_size: int, device: str) -> float:
    model.to(device)

    total = len(frames)
    batches = [frames[i : i + batch_size] for i in range(0, total, batch_size)]

    # Warm-up pass (not timed)
    model(batches[0], verbose=False)
    if device != "cpu":
        torch.cuda.synchronize()

    start = time.perf_counter()
    for batch in batches:
        model(batch, verbose=False)
    if device != "cpu":
        torch.cuda.synchronize()
    elapsed = time.perf_counter() - start

    return elapsed


def main():
    args = parse_args()

    print(f"PyTorch version : {torch.__version__}")
    print(f"CUDA available  : {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"GPU             : {torch.cuda.get_device_name(0)}")
    print()

    frames = make_synthetic_frames(args.frames, args.imgsz)
    print(f"Model           : {args.model}")
    print(f"Frames          : {args.frames}  |  Batch size: {args.batch_size}  |  Image size: {args.imgsz}")
    print()

    model = YOLO(args.model)

    # --- CPU run ---
    print("Running on CPU...")
    cpu_time = run_benchmark(model, frames, args.batch_size, "cpu")
    cpu_fps = args.frames / cpu_time
    print(f"  {cpu_time:.2f}s  ({cpu_fps:.1f} fps)")

    # --- GPU run (if available and not suppressed) ---
    if torch.cuda.is_available() and not args.cpu_only:
        print("Running on GPU...")
        gpu_time = run_benchmark(model, frames, args.batch_size, "cuda")
        gpu_fps = args.frames / gpu_time
        print(f"  {gpu_time:.2f}s  ({gpu_fps:.1f} fps)")
        print()
        print(f"Speedup: {cpu_time / gpu_time:.1f}x")
    else:
        if args.cpu_only:
            print("GPU skipped (--cpu-only flag set).")
        else:
            print("No GPU detected — skipping GPU benchmark.")


if __name__ == "__main__":
    main()
