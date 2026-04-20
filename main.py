from utils import (read_video,
                   save_video,
                   measure_distance,
                   draw_player_stats,
                   convert_pixel_distance_to_meters,
                   save_shot_heatmap
                   )
import constants
import os
from trackers import PlayerTracker,BallTracker
from court_line_detector import CourtLineDetector
from mini_court import MiniCourt
import cv2
import pandas as pd
from copy import deepcopy


def main(
    input_video_path: str = "input_videos/input_video.mp4",
    output_video_path: str = None,
    heatmap_output_path: str = None,
    progress_callback=None,
):
    def progress(msg):
        if progress_callback:
            progress_callback(msg)

    # Read Video
    progress("Reading video frames...")
    video_frames = read_video(input_video_path)

    if not video_frames:
        raise FileNotFoundError(f"No frames read from '{input_video_path}'. Check that the file exists and is a valid video.")

    cap = cv2.VideoCapture(input_video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    cap.release()

    # Detect Players and Ball
    progress("Detecting players...")
    player_tracker = PlayerTracker(model_path='yolov8x')
    ball_tracker = BallTracker(model_path='models/yolo5_last.pt')

    video_name = os.path.splitext(os.path.basename(input_video_path))[0]
    if output_video_path is None:
        output_video_path = f"output_videos/{video_name}.mp4"
    if heatmap_output_path is None:
        heatmap_output_path = f"output_visuals/{video_name}.png"
    player_detections = player_tracker.detect_frames(video_frames,
                                                     stub_path=f"tracker_stubs/{video_name}_player_detections.pkl"
                                                     )
    progress("Detecting ball...")
    ball_detections = ball_tracker.detect_frames(video_frames,
                                                     stub_path=f"tracker_stubs/{video_name}_ball_detections.pkl"
                                                     )
    ball_detections = ball_tracker.interpolate_ball_positions(ball_detections)


    # Court Line Detector model
    progress("Detecting court lines...")
    court_model_path = "models/keypoints_model.pth"
    court_line_detector = CourtLineDetector(court_model_path)
    court_keypoints = court_line_detector.predict(video_frames[0])

    # choose players
    player_detections = player_tracker.choose_and_filter_players(court_keypoints, player_detections)

    # MiniCourt
    mini_court = MiniCourt(video_frames[0])

    # Detect ball shots
    ball_shot_frames= ball_tracker.get_ball_shot_frames(ball_detections)

    # Convert positions to mini court positions
    progress("Computing mini court positions...")
    player_mini_court_detections, ball_mini_court_detections = mini_court.convert_bounding_boxes_to_mini_court_coordinates(player_detections,
                                                                                                          ball_detections,
                                                                                                          court_keypoints)

    progress("Calculating player stats...")
    player_stats_data = [{
        'frame_num':0,
        'player_1_number_of_shots':0,
        'player_1_total_shot_speed':0,
        'player_1_last_shot_speed':0,
        'player_1_total_player_speed':0,
        'player_1_last_player_speed':0,

        'player_2_number_of_shots':0,
        'player_2_total_shot_speed':0,
        'player_2_last_shot_speed':0,
        'player_2_total_player_speed':0,
        'player_2_last_player_speed':0,
    } ]

    per_shot_rows = []
    rally_number = 1

    for ball_shot_ind in range(len(ball_shot_frames)-1):
        start_frame = ball_shot_frames[ball_shot_ind]
        end_frame = ball_shot_frames[ball_shot_ind+1]
        ball_shot_time_in_seconds = (end_frame-start_frame)/fps

        # Get distance covered by the ball
        distance_covered_by_ball_pixels = measure_distance(ball_mini_court_detections[start_frame][1],
                                                           ball_mini_court_detections[end_frame][1])
        distance_covered_by_ball_meters = convert_pixel_distance_to_meters( distance_covered_by_ball_pixels,
                                                                           constants.DOUBLE_LINE_WIDTH,
                                                                           mini_court.get_width_of_mini_court()
                                                                           )

        # Speed of the ball shot in km/h
        speed_of_ball_shot = distance_covered_by_ball_meters/ball_shot_time_in_seconds * 3.6

        # player who hit the ball
        player_positions = player_mini_court_detections[start_frame]
        if not player_positions or not player_mini_court_detections[end_frame]:
            continue
        player_shot_ball = min( player_positions.keys(), key=lambda player_id: measure_distance(player_positions[player_id],
                                                                                                 ball_mini_court_detections[start_frame][1]))

        opponent_player_id = 1 if player_shot_ball == 2 else 2

        # speed of both players during this interval
        def player_speed(pid):
            d_pixels = measure_distance(player_mini_court_detections[start_frame][pid],
                                        player_mini_court_detections[end_frame][pid])
            d_meters = convert_pixel_distance_to_meters(d_pixels,
                                                        constants.DOUBLE_LINE_WIDTH,
                                                        mini_court.get_width_of_mini_court())
            return d_meters / ball_shot_time_in_seconds * 3.6

        speed_of_opponent = player_speed(opponent_player_id)
        speed_of_hitter   = player_speed(player_shot_ball)

        # ball lands at end_frame position — check if in bounds
        ball_landing_position = ball_mini_court_detections[end_frame][1]
        in_bounds = mini_court.is_ball_in_bounds(ball_landing_position)

        per_shot_rows.append({
            'shot_number':       ball_shot_ind + 1,
            'frame_num':         start_frame,
            'hitting_player':    player_shot_ball,
            'ball_speed_kmh':    round(speed_of_ball_shot, 2),
            'player_1_speed_kmh': round(speed_of_hitter   if player_shot_ball == 1 else speed_of_opponent, 2),
            'player_2_speed_kmh': round(speed_of_hitter   if player_shot_ball == 2 else speed_of_opponent, 2),
            'ball_in_bounds':    in_bounds,
            'rally_number':      rally_number,
        })

        if not in_bounds:
            rally_number += 1

        current_player_stats= deepcopy(player_stats_data[-1])
        current_player_stats['frame_num'] = start_frame
        current_player_stats[f'player_{player_shot_ball}_number_of_shots'] += 1
        current_player_stats[f'player_{player_shot_ball}_total_shot_speed'] += speed_of_ball_shot
        current_player_stats[f'player_{player_shot_ball}_last_shot_speed'] = speed_of_ball_shot

        current_player_stats[f'player_{opponent_player_id}_total_player_speed'] += speed_of_opponent
        current_player_stats[f'player_{opponent_player_id}_last_player_speed'] = speed_of_opponent

        player_stats_data.append(current_player_stats)

    player_stats_data_df = pd.DataFrame(player_stats_data)
    frames_df = pd.DataFrame({'frame_num': list(range(len(video_frames)))})
    player_stats_data_df = pd.merge(frames_df, player_stats_data_df, on='frame_num', how='left')
    player_stats_data_df = player_stats_data_df.ffill()

    player_stats_data_df['player_1_average_shot_speed'] = player_stats_data_df['player_1_total_shot_speed']/player_stats_data_df['player_1_number_of_shots']
    player_stats_data_df['player_2_average_shot_speed'] = player_stats_data_df['player_2_total_shot_speed']/player_stats_data_df['player_2_number_of_shots']
    player_stats_data_df['player_1_average_player_speed'] = player_stats_data_df['player_1_total_player_speed']/player_stats_data_df['player_2_number_of_shots']
    player_stats_data_df['player_2_average_player_speed'] = player_stats_data_df['player_2_total_player_speed']/player_stats_data_df['player_1_number_of_shots']

    # Write CSVs
    os.makedirs("output_videos", exist_ok=True)
    per_shot_df = pd.DataFrame(per_shot_rows)
    per_shot_df.to_csv(f"output_csv/{video_name}_per_shot_stats.csv", index=False)

    if per_shot_rows:
        rally_lengths = per_shot_df.groupby('rally_number').size()
        summary_rows = []
        for pid in [1, 2]:
            p_shots = per_shot_df[per_shot_df['hitting_player'] == pid]
            speed_col = f'player_{pid}_speed_kmh'
            summary_rows.append({
                'player':                pid,
                'total_shots':           len(p_shots),
                'errors':                int((~p_shots['ball_in_bounds']).sum()),
                'in_bounds_shots':       int(p_shots['ball_in_bounds'].sum()),
                'avg_shot_speed_kmh':    round(p_shots['ball_speed_kmh'].mean(), 2) if len(p_shots) else 0,
                'max_shot_speed_kmh':    round(p_shots['ball_speed_kmh'].max(),  2) if len(p_shots) else 0,
                'avg_player_speed_kmh':  round(per_shot_df[speed_col].mean(),    2),
                'max_player_speed_kmh':  round(per_shot_df[speed_col].max(),     2),
            })
        summary_df = pd.DataFrame(summary_rows)
        summary_df['total_rallies']      = len(rally_lengths)
        summary_df['longest_rally']      = int(rally_lengths.max())
        summary_df['avg_rally_length']   = round(rally_lengths.mean(), 2)
        summary_df['total_shots_match']  = len(per_shot_df)
        summary_df.to_csv(f"output_csv/{video_name}_match_summary.csv", index=False)



    # Draw output
    progress("Rendering output video...")
    ## Draw Player Bounding Boxes
    output_video_frames= player_tracker.draw_bboxes(video_frames, player_detections)
    output_video_frames= ball_tracker.draw_bboxes(output_video_frames, ball_detections)

    ## Draw court Keypoints
    output_video_frames  = court_line_detector.draw_keypoints_on_video(output_video_frames, court_keypoints)

    # Draw Mini Court
    output_video_frames = mini_court.draw_mini_court(output_video_frames)
    output_video_frames = mini_court.draw_points_on_mini_court(output_video_frames,player_mini_court_detections)
    output_video_frames = mini_court.draw_points_on_mini_court(output_video_frames,ball_mini_court_detections, color=(0,255,255))    

    # Draw Player Stats
    output_video_frames = draw_player_stats(output_video_frames,player_stats_data_df)

    ## Draw frame number on top left corner
    for i, frame in enumerate(output_video_frames):
        cv2.putText(frame, f"Frame: {i}",(10,30),cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    progress("Saving video...")
    save_video(output_video_frames, output_video_path, fps)

    progress("Saving heatmap...")
    save_shot_heatmap(ball_mini_court_detections, ball_shot_frames, mini_court, heatmap_output_path)

if __name__ == "__main__":
    main()