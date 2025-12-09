# backend/integrations/pika_client.py
import os
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

import requests

# If using Fal.ai wrapper for Pika [web:89][web:146]:
FAL_API_KEY = os.getenv("FAL_API_KEY", "")
FAL_BASE_URL = "https://fal.run"  # Fal base; the exact URL/path depends on client [web:89][web:140]

MEDIA_ROOT = Path("media")
CLIPS_DIR = MEDIA_ROOT / "clips"
CLIPS_DIR.mkdir(parents=True, exist_ok=True)


def _fake_generate_clip(prompt: str, idx: int, job_id: str) -> str:
    """
    Stand-in for Pika. Creates an empty placeholder file so the pipeline runs.
    """
    path = CLIPS_DIR / f"{job_id}_scene_{idx}.mp4"
    # Just touch the file for now
    path.write_bytes(b"")
    return str(path)


def generate_clip_with_pika(scene: Dict[str, Any], job_id: str) -> str:
    """
    Call real Pika via Fal, or fall back to a fake clip if API key not set.
    scene: {index, prompt, duration, aspect_ratio}
    Returns local file path to the downloaded clip.
    """
    if not FAL_API_KEY:
        # No API key yet → fake file path
        return _fake_generate_clip(scene["prompt"], scene["index"], job_id)

    headers = {
        "Authorization": f"Key {FAL_API_KEY}",
        "Content-Type": "application/json",
    }

    # Example Fal Pika v2.1 text-to-video params [web:89][web:140]
    payload = {
        "input": {
            "prompt": scene["prompt"],
            "duration": str(scene["duration"]),  # e.g. "5" or "10"
            "aspect_ratio": scene.get("aspect_ratio", "16:9"),
            "resolution": "720p",
        }
    }

    # Submit request (exact path may differ per Fal client) [web:89][web:140]
    submit_url = f"{FAL_BASE_URL}/queue/fal-ai/pika/v2.1/text-to-video"
    resp = requests.post(submit_url, json=payload, headers=headers, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    request_id: str = data["request_id"]

    # Poll result (simplified)
    result_url = f"{FAL_BASE_URL}/queue/fal-ai/pika/v2.1/text-to-video/{request_id}"
    while True:
        r = requests.get(result_url, headers=headers, timeout=60)
        r.raise_for_status()
        rd = r.json()
        status = rd.get("status")
        if status == "COMPLETED":
            break
        elif status in ("FAILED", "CANCELLED"):
            raise RuntimeError(f"Pika generation failed: {rd}")
        time.sleep(2)

    # Fal output schema includes video URL in `data` (check docs) [web:89][web:140]
    video_url: Optional[str] = rd.get("data", {}).get("video_url")
    if not video_url:
        raise RuntimeError(f"No video_url in Pika result: {rd}")

    # Download video to local file
    clip_path = CLIPS_DIR / f"{job_id}_scene_{scene['index']}.mp4"
    vr = requests.get(video_url, timeout=300)
    vr.raise_for_status()
    clip_path.write_bytes(vr.content)
    return str(clip_path)
