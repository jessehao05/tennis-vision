import os
import numpy as np
import cv2
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


def save_shot_heatmap(ball_mini_court_detections, ball_shot_frames, mini_court, output_path):
    canvas_h = mini_court.drawing_rectangle_height
    canvas_w = mini_court.drawing_rectangle_width
    offset_x = mini_court.start_x
    offset_y = mini_court.start_y

    # Accumulate landing positions into a density grid.
    # The ball lands just before the next shot frame, so we use ball_shot_frames[i+1]
    # as the landing position of the shot that started at ball_shot_frames[i].
    density = np.zeros((canvas_h, canvas_w), dtype=np.float32)
    for i in range(len(ball_shot_frames) - 1):
        frame_idx = ball_shot_frames[i + 1]
        if frame_idx < len(ball_mini_court_detections) and 1 in ball_mini_court_detections[frame_idx]:
            x, y = ball_mini_court_detections[frame_idx][1]
            px = int(x - offset_x)
            py = int(y - offset_y)
            if 0 <= px < canvas_w and 0 <= py < canvas_h:
                density[py, px] += 1

    density = cv2.GaussianBlur(density, (31, 31), 0)

    fig, ax = plt.subplots(figsize=(4, 8))
    ax.set_facecolor('#f0f0f0')

    if density.max() > 0:
        im = ax.imshow(
            density,
            cmap='hot',
            interpolation='bilinear',
            origin='upper',
            extent=[0, canvas_w, canvas_h, 0],
            alpha=0.85,
            vmin=0,
        )
        plt.colorbar(im, ax=ax, label='Shot Density', fraction=0.046, pad=0.04)

    # Helper to get a keypoint in canvas-relative coords
    kp = mini_court.drawing_key_points
    def kp_xy(i):
        return (kp[i * 2] - offset_x, kp[i * 2 + 1] - offset_y)

    # Draw court lines
    for line in mini_court.lines:
        p1 = kp_xy(line[0])
        p2 = kp_xy(line[1])
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color='white', linewidth=1.5, zorder=2)

    # Draw net (horizontal line at vertical midpoint between top and bottom baselines)
    net_y = (kp_xy(0)[1] + kp_xy(2)[1]) / 2
    ax.plot([kp_xy(0)[0], kp_xy(1)[0]], [net_y, net_y], color='deepskyblue', linewidth=2, zorder=3, label='Net')

    ax.set_xlim(0, canvas_w)
    ax.set_ylim(canvas_h, 0)
    ax.set_title('Ball Landing Placement Heatmap', fontsize=13, fontweight='bold')
    ax.set_xlabel('Court Width (px)')
    ax.set_ylabel('Court Length (px)')
    ax.legend(loc='upper right', fontsize=8)

    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Heatmap saved to {output_path}")
