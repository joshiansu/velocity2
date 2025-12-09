# backend/pipelines/video_pipeline.py
# import uuid
# from pathlib import Path
# from typing import Dict, Any, List

# from moviepy.editor import VideoFileClip, concatenate_videoclips  # [web:27][web:92]

# from backend.agents.scene_agent import storyboard_to_scene_prompts
# from backend.integrations.pika_client import generate_clip_with_pika

# MEDIA_ROOT = Path("media")
# FINAL_DIR = MEDIA_ROOT / "final"
# FINAL_DIR.mkdir(parents=True, exist_ok=True)


# def generate_video_from_storyboard_old(
#     storyboard: Dict[str, Any],
#     product_description: str,
# ) -> Dict[str, Any]:
#     """
#     Orchestrates: storyboard -> scene prompts -> Pika clips -> stitched final video.
#     Returns metadata with paths.
#     """
#     job_id = str(uuid.uuid4())

#     # 1) storyboard -> scene prompts
#     scenes = storyboard_to_scene_prompts(storyboard, product_description)

#     # 2) generate clips for each scene
#     clip_paths: List[str] = []
#     for scene in scenes:
#         clip_path = generate_clip_with_pika(scene, job_id=job_id)
#         clip_paths.append(clip_path)

#     # 3) stitch clips
#     clips = []
#     for path in clip_paths:
#         if not Path(path).exists():
#             continue
#         clips.append(VideoFileClip(path))

#     if not clips:
#         raise RuntimeError("No clips generated for video")

#     final_clip = concatenate_videoclips(clips, method="compose")
#     final_path = FINAL_DIR / f"{job_id}_final.mp4"
#     final_clip.write_videofile(str(final_path), codec="libx264")  # [web:27][web:147]

#     # Close clips to release file handles
#     for c in clips:
#         c.close()
#     final_clip.close()

#     return {
#         "job_id": job_id,
#         "scene_count": len(scenes),
#         "clip_paths": clip_paths,
#         "final_video_path": str(final_path),
#     }

# backend/pipelines/video_pipeline.py
import subprocess
import uuid
from pathlib import Path
from typing import Dict, Any, List

from backend.agents.scene_agent import storyboard_to_scene_prompts
from backend.integrations.pika_client import generate_clip_with_pika
from backend.integrations.video_client import generate_clip

MEDIA_ROOT = Path("media")
FINAL_DIR = MEDIA_ROOT / "final"
FINAL_DIR.mkdir(parents=True, exist_ok=True)


def concat_videos_ffmpeg(input_files: List[str], output_file: str) -> None:
    """
    Concatenate MP4 files using ffmpeg concat demuxer.
    Creates a temporary file list and runs:
      ffmpeg -f concat -safe 0 -i list.txt -c copy output.mp4
    [web:149][web:150][web:152]
    """
    if not input_files:
        raise ValueError("No input files for concatenation")

    list_path = Path(output_file).with_suffix(".txt")
    with list_path.open("w") as f:
        for p in input_files:
            f.write(f"file '{Path(p).resolve()}'\n")

    cmd = [
        "ffmpeg",
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(list_path),
        "-c", "copy",
        output_file,
    ]
    # Run ffmpeg and raise if it fails
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    list_path.unlink(missing_ok=True)


def generate_video_from_storyboard(
    storyboard: Dict[str, Any],
    product_description: str,
) -> Dict[str, Any]:
    """
    Orchestrates: storyboard -> scene prompts -> Pika clips -> stitched final video via ffmpeg.
    """
    job_id = str(uuid.uuid4())

    # 1) storyboard -> scene prompts
    scenes = storyboard_to_scene_prompts(storyboard, product_description)

    # 2) generate clips for each scene
    clip_paths: List[str] = []
    for scene in scenes:
        # clip_path = generate_clip_with_pika(scene, job_id=job_id)
        

        # ...
        clip_path = generate_clip(scene, job_id=job_id)

        clip_paths.append(clip_path)

    # 3) stitch clips via ffmpeg
    final_path = FINAL_DIR / f"{job_id}_final.mp4"
    print("CLip paths", clip_paths)
    concat_videos_ffmpeg(clip_paths, str(final_path))

    return {
        "job_id": job_id,
        "scene_count": len(scenes),
        "clip_paths": clip_paths,
        "final_video_path": str(final_path),
    }

