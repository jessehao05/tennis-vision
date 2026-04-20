import cv2
import subprocess
import os
import shutil
import glob

def _find_ffmpeg():
    found = shutil.which("ffmpeg")
    if found:
        return found
    # Fallback: winget install location
    pattern = os.path.expanduser(
        r"~\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg*\ffmpeg-*\bin\ffmpeg.exe"
    )
    matches = glob.glob(pattern)
    if matches:
        return matches[0]
    raise FileNotFoundError("ffmpeg not found. Install it and add to PATH.")

_FFMPEG = _find_ffmpeg()

def read_video(video_path):
    cap = cv2.VideoCapture(video_path)
    frames = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
    cap.release()
    return frames

def save_video(output_video_frames, output_video_path, fps=24):
    tmp_path = output_video_path + ".tmp.mp4"
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(tmp_path, fourcc, fps, (output_video_frames[0].shape[1], output_video_frames[0].shape[0]))
    for frame in output_video_frames:
        out.write(frame)
    out.release()

    # Re-encode to H.264 for browser compatibility
    subprocess.run(
        [_FFMPEG, "-y", "-i", tmp_path, "-vcodec", "libx264", "-pix_fmt", "yuv420p", output_video_path],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    os.remove(tmp_path)
    print(f"Output video saved to {output_video_path}")