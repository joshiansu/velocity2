# backend/integrations/video_client.py
import os
import time
from pathlib import Path
from typing import Dict, Any

import requests

MEDIA_ROOT = Path("media")
CLIPS_DIR = MEDIA_ROOT / "clips"
CLIPS_DIR.mkdir(parents=True, exist_ok=True)

VIDEO_PROVIDER = os.getenv("VIDEO_PROVIDER", "mock")  # "mock", "runway", "luma"


def generate_clip(scene: Dict[str, Any], job_id: str) -> str:
    """
    Dispatch based on VIDEO_PROVIDER.
    scene: {index, prompt, duration, aspect_ratio}
    Returns local mp4 path.
    """
    provider = VIDEO_PROVIDER.lower()
    print("provider", provider)
    provider = "mock"
    if provider == "runway":
        return _generate_clip_runway(scene, job_id)
    elif provider == "luma":
        return _generate_clip_luma(scene, job_id)
    else:
        return _generate_clip_mock(scene, job_id)

RUNWAY_API_KEY = os.getenv("RUNWAY_API_KEY", "")
RUNWAY_BASE_URL = "https://api.runwayml.com/v1"  # check docs [web:216]


def _runway_headers() -> Dict[str, str]:
    if not RUNWAY_API_KEY:
        raise RuntimeError("RUNWAY_API_KEY not set")
    return {
        "Authorization": f"Bearer {RUNWAY_API_KEY}",
        "Content-Type": "application/json",
    }


def _generate_clip_runway(scene: Dict[str, Any], job_id: str) -> str:
    """
    Example: Runway text-to-video.
    You MUST adapt endpoint path and payload fields to the current Runway docs. [web:216]
    """
    prompt = scene["prompt"]
    duration = scene["duration"]  # seconds
    aspect = scene.get("aspect_ratio", "16:9")

    # 1) Submit job
    submit_url = f"{RUNWAY_BASE_URL}/videos"  # example path; confirm in docs [web:216]
    payload = {
        "prompt": prompt,
        "duration": duration,
        "aspect_ratio": aspect,
        # add model/version fields as per Runway docs
    }
    resp = requests.post(submit_url, json=payload, headers=_runway_headers(), timeout=60)
    resp.raise_for_status()
    data = resp.json()
    job_id_runway = data.get("id") or data.get("job_id")

    # 2) Poll until done
    status_url = f"{RUNWAY_BASE_URL}/videos/{job_id_runway}"  # example path [web:216]
    while True:
        r = requests.get(status_url, headers=_runway_headers(), timeout=30)
        r.raise_for_status()
        jd = r.json()
        status = jd.get("status")
        if status in ("completed", "succeeded"):
            break
        if status in ("failed", "error"):
            raise RuntimeError(f"Runway generation failed: {jd}")
        time.sleep(3)

    # 3) Download video URL
    video_url = jd.get("output", {}).get("url") or jd.get("video_url")
    if not video_url:
        raise RuntimeError(f"No video URL in Runway result: {jd}")
    clip_path = CLIPS_DIR / f"{job_id}_scene_{scene['index']}.mp4"
    vr = requests.get(video_url, timeout=300)
    vr.raise_for_status()
    clip_path.write_bytes(vr.content)
    return str(clip_path)


from shutil import copyfile

SAMPLE_DIR = MEDIA_ROOT / "sample"
SAMPLE_CLIP = SAMPLE_DIR / "sample.mp4"  # put any valid test mp4 here


def _generate_clip_mock(scene: Dict[str, Any], job_id: str) -> str:
    if not SAMPLE_CLIP.exists():
        raise RuntimeError(f"Sample clip not found at {SAMPLE_CLIP}")
    out_path = CLIPS_DIR / f"{job_id}_scene_{scene['index']}.mp4"
    copyfile(SAMPLE_CLIP, out_path)
    return str(out_path)

LUMA_API_KEY = os.getenv("LUMA_API_KEY", "")
LUMA_BASE_URL = "https://api.piapi.ai/api/v1/task"  # replace with real base [web:200][web:203]


def _luma_headers() -> Dict[str, str]:
    if not LUMA_API_KEY:
        raise RuntimeError("LUMA_API_KEY not set")
    return {
        "Authorization": f"Bearer {LUMA_API_KEY}",  # or "x-api-key": ...
        "Content-Type": "application/json",
    }


# def _generate_clip_luma(scene: Dict[str, Any], job_id: str) -> str:
#     prompt = scene["prompt"]
#     duration = scene["duration"]
#     aspect = scene.get("aspect_ratio", "16:9")

#     # 1) Submit job (path and schema from your provider’s docs) [web:199][web:203]
#     submit_url = f"{LUMA_BASE_URL}/dream-machine/generations"
#     payload = {
#         "prompt": prompt,
#         "duration": duration,
#         "aspect_ratio": aspect,
#         # add fields like "quality", "seed", etc., as required
#     }
#     resp = requests.post(submit_url, json=payload, headers=_luma_headers(), timeout=60)
#     resp.raise_for_status()
#     data = resp.json()
#     gen_id = data.get("id") or data.get("generation_id")

#     # 2) Poll job status
#     status_url = f"{LUMA_BASE_URL}/dream-machine/generations/{gen_id}"
#     while True:
#         r = requests.get(status_url, headers=_luma_headers(), timeout=30)
#         r.raise_for_status()
#         jd = r.json()
#         status = jd.get("status")
#         if status in ("completed", "succeeded"):
#             break
#         if status in ("failed", "error"):
#             raise RuntimeError(f"Luma generation failed: {jd}")
#         time.sleep(3)

#     # 3) Download video
#     video_url = jd.get("output", {}).get("video_url") or jd.get("video_url")
#     if not video_url:
#         raise RuntimeError(f"No video URL in Luma result: {jd}")
#     clip_path = CLIPS_DIR / f"{job_id}_scene_{scene['index']}.mp4"
#     vr = requests.get(video_url, timeout=300)
#     vr.raise_for_status()
#     clip_path.write_bytes(vr.content)
#     return str(clip_path)


# backend/integrations/video_client.py
import os
import time
from pathlib import Path
from typing import Dict, Any

import requests

MEDIA_ROOT = Path("media")
CLIPS_DIR = MEDIA_ROOT / "clips"
CLIPS_DIR.mkdir(parents=True, exist_ok=True)

PIAPI_KEY = "b9ba07821766bbf16345d0965a0b3a88efa34027e132e4ffdfad8ee841746b54"#os.getenv("PIAPI_API_KEY", "")  # set this in your env
PIAPI_BASE_URL = "https://api.piapi.ai"


def _piapi_headers() -> Dict[str, str]:
    if not PIAPI_KEY:
        raise RuntimeError("PIAPI_API_KEY not set")
    return {
        "x-api-key": PIAPI_KEY,  # header name from spec
        "Content-Type": "application/json",
    }


def _generate_clip_luma(scene: Dict[str, Any], job_id: str) -> str:
    """
    Text-to-video using Luma Dream Machine via PiAPI.
    Uses POST /api/v1/task with model=luma, task_type=video_generation.
    """
    prompt = scene["prompt"]
    duration = scene["duration"]  # must be 5 or 10
    aspect = scene.get("aspect_ratio", "16:9")

    # 1) Create task
    create_url = f"{PIAPI_BASE_URL}/api/v1/task"
    payload = {
        "model": "luma",
        "task_type": "video_generation",
        "input": {
            "prompt": prompt,
            "model_name": "ray-v1",   # or "ray-v2" if you prefer
            "duration": 5 if duration <= 5 else 10,
            "aspect_ratio": aspect,   # one of '9:16','3:4','1:1','4:3','16:9','21:9'
        },
        # "config": { ... }  # optional webhook_config/service_mode if you want
    }
    headers = _piapi_headers()
    print("payload", payload)
    print("_piapi_headers()", headers)
    resp = requests.post(create_url, json=payload, headers=headers, timeout=60)
    print("PiAPI STATUS:", resp.status_code)
    print("PiAPI BODY:", resp.text)
    resp.raise_for_status()
    data = resp.json()

    # According to spec, task_id is in data.data.task_id
    task_id = data["data"]["task_id"]

    # 2) Poll task status until Completed / Failed
    status_url = f"{PIAPI_BASE_URL}/api/v1/task/{task_id}"
    while True:
        r = requests.get(status_url, headers=_piapi_headers(), timeout=30)
        r.raise_for_status()
        jd = r.json()
        status = jd["data"]["status"]
        if status == "Completed":
            break
        if status == "Failed":
            raise RuntimeError(f"Luma task failed: {jd['data'].get('error')}")
        time.sleep(3)

    # 3) Extract video URL from output
    output = jd["data"]["output"]
    # Consult PiAPI docs for actual field; likely something like:
    # output["video"] or output["video_raw"] or output["thumbnail"]
    video_url = output.get("video") or output.get("video_raw")
    if not video_url:
        raise RuntimeError(f"No video URL in Luma output: {output}")

    # 4) Download to local file
    clip_path = CLIPS_DIR / f"{job_id}_scene_{scene['index']}.mp4"
    vr = requests.get(video_url, timeout=300)
    vr.raise_for_status()
    clip_path.write_bytes(vr.content)

    return str(clip_path)


def create_luma_video(prompt):
    import requests
    import json

    url = "https://api.piapi.ai/api/v1/task"

    payload = json.dumps({
    "model": "luma",
    "task_type": "video_generation",
    "input": {
        "prompt": "Fly fishing",
        "key_frames": {
            "frame0": {
                "type": "laborum ad",
                "url": "https://glaring-fishery.com/",
                "id": "XFT5J9GBfGDm_iqe4z3oU"
            },
            "frame1": {
                "type": "do ex dolor ea",
                "url": "https://hungry-oil.org/"
            }
        },
        "model_name": "ray-v1",
        "duration": 5,
        "aspect_ratio": "9:16"
    },
    "config": {
        "webhook_config": {
            "endpoint": "",
            "secret": ""
        },
        "service_mode": ""
    }
    })
    headers = {
    'x-api-key': '',
    'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    print(response.text)
    return response.text
