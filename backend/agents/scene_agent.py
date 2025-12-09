# backend/agents/scene_agent.py
from typing import Dict, Any, List


def shot_to_prompt(shot: Dict[str, Any], product_description: str) -> str:
    """
    Turn a storyboard shot into a Pika-friendly text prompt.
    Keep it short and visual; no JSON here.
    """
    shot_type = shot.get("type", "")
    camera = shot.get("camera", "")
    context = shot.get("context", "")
    focus = shot.get("focus", "")
    caption = shot.get("caption") or shot.get("overlay") or ""

    parts: List[str] = []

    if shot_type:
        parts.append(f"{shot_type} shot")
    if camera:
        parts.append(camera)
    if context:
        parts.append(f"in {context}")
    if focus:
        parts.append(f"focused on {focus}")

    # Add product + style conditioning
    parts.append(f"high quality cinematic ad of {product_description}")
    if caption:
        parts.append(f"with on-screen text: \"{caption}\"")

    # Join into one sentence
    return ", ".join(p for p in parts if p)


def storyboard_to_scene_prompts(
    storyboard: Dict[str, Any],
    product_description: str,
    default_aspect_ratio: str = "16:9",
    default_duration: int = 5,
) -> List[Dict[str, Any]]:
    """
    Convert storyboard JSON into a list of scene generation requests.
    Each scene request will later be sent to Pika.
    """
    print("storyboard", storyboard)
    print(type(storyboard))
    shots = storyboard.get("shots", [])
    scenes = []

    for idx, shot in enumerate(shots):
        duration = int(round(shot.get("duration", default_duration)))
        # Clamp to Pika-supported durations (e.g. 5 or 10 seconds via Fal) [web:89][web:139]
        if duration <= 5:
            duration = 5
        else:
            duration = 10

        prompt = shot_to_prompt(shot, product_description)

        scenes.append(
            {
                "index": idx,
                "prompt": prompt,
                "duration": duration,
                "aspect_ratio": default_aspect_ratio,
            }
        )

    return scenes
