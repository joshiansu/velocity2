# # backend/agents/planner.py
import base64
import json
import os
from typing import Any, Dict

import requests

GROK_API_KEY = os.getenv("GROK_API_KEY", "")
# GROK_URL = "https://api.x.ai/v1/chat/completions"  # xAI Grok API base [web:16]

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {GROK_API_KEY}",
}


def _encode_image_bytes(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode("utf-8")


# # def ex# backend/agents/planner.py (replace extract_product_attributes)

def extract_product_attributes(image_bytes: bytes) -> str:
    """
    Use Grok vision model to describe the product in the image.
    """
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")
    data_url = f"data:image/png;base64,{image_b64}"  # or jpeg depending on upload

    payload = {
        "model": "grok-vision-beta",  # replace with the actual vision model id you have access to [web:38][web:48]
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Describe this product in rich detail for an e-commerce video advertisement.",
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": data_url
                        },
                    },
                ],
            }
        ],
    }

    resp = requests.post(GROK_URL, headers=HEADERS, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]


# def plan_storyboard(product_description: str, max_scenes: int = 4) -> Dict[str, Any]:
#     """
#     Use Grok text model to produce a JSON storyboard.
#     """
#     system_instruction = f"""
# You are a senior creative director for e-commerce video ads.
# You MUST produce a JSON storyboard for a 6–10 second video ad.
# Exactly {max_scenes} shots. Only valid JSON. No comments. No trailing commas.
# Keys: type, duration, camera, context, focus, caption (optional), overlay (for CTA), cta_position (for CTA).
# """

#     user_prompt = f"""
# Product details:
# {product_description}

# Generate a high-conversion ad storyboard including camera motion, duration,
# scene context, and CTA if applicable. Ensure pure JSON in your reply.
# """

#     payload = {
#         "model": "grok-2-latest",  # adjust to your available Grok model [web:16]
#         "messages": [
#             {"role": "system", "content": system_instruction},
#             {"role": "user", "content": user_prompt},
#         ],
#         "temperature": 0.3,
#     }

#     resp = requests.post(GROK_URL, headers=HEADERS, json=payload, timeout=60)
#     resp.raise_for_status()
#     data = resp.json()
#     content = data["choices"][0]["message"]["content"]
#     # Model should output pure JSON; `json.loads` will fail fast if not.
#     return json.loads(content)
# # backend/agents/planner.py
def extract_product_attributes_from_text(prompt: str) -> str:
    # For now, just echo – acts as “product description”
    return prompt


# backend/agents/planner.py
import json
import os
import requests
from typing import Any, Dict

import json
import re
from typing import Any, Dict
from backend.agents.llm_client import chat

GROK_API_KEY = os.getenv("GROK_API_KEY", "")
GROK_URL = "https://api.x.ai/v1/chat/completions"

GROK_API_KEY = os.getenv("GROK_API_KEY", "")

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {GROK_API_KEY}",
}

def _extract_json_block(text: str) -> str:
    """
    Extract JSON object from an LLM response that may include markdown fences
    or extra text.
    """
    # 1. Try to find markdown code block with 'json' language or just backticks
    # Matches ```json ... ``` or just ``` ... ```
    m = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1).strip()

    # 2. Naive finding of first { and last }
    start = text.find("{")
    end = text.rfind("}")
    
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]

    return text.strip()


def _critique_storyboard(draft_storyboard: str, product_description: str) -> str:
    """
    Ask the LLM to critique the draft storyboard for improvements.
    """
    system_instruction = (
        "You are a critical film editor. Analyze the given video storyboard draft. "
        "Identify 3 key areas to improve for better flow, engagement, and visual impact. "
        "Focus on: 1) Pacing, 2) Visual variety (camera angles), 3) Clarity of the CTA. "
        "Be concise."
    )
    
    user_prompt = (
        f"Product: {product_description}\n\n"
        f"Draft Storyboard:\n{draft_storyboard}\n\n"
        "Provide a short critique."
    )
    
    return chat(
        [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.3
    )


def _refine_storyboard(draft_storyboard: str, critique: str, product_description: str, max_scenes: int) -> str:
    """
    Ask the LLM to rewrite the storyboard based on the critique.
    """
    system_instruction = (
        "You are a master storyboard artist. "
        f"Rewrite the storyboard to address the critique, producing the FINAL version with exactly {max_scenes} shots. "
        "Return ONLY valid JSON. No markdown formatting, no comments."
    )
    
    user_prompt = (
        f"Original Draft:\n{draft_storyboard}\n\n"
        f"Critique to Address:\n{critique}\n\n"
        "Generate the polished, final JSON storyboard."
    )
    
    return chat(
        [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.2 # Lower temp for precision in JSON generation
    )


def plan_storyboard(product_description: str, max_scenes: int = 4) -> Dict[str, Any]:
    system_instruction = (
        "You are a senior creative director for e-commerce video ads. "
        f"You MUST produce a JSON storyboard for a 6–10 second video ad with exactly {max_scenes} shots. "
        "Only return valid JSON with a top-level 'shots' array. No comments, no explanations."
    )

    user_prompt = (
        "Product details:\n"
        f"{product_description}\n\n"
        "Generate a high-conversion video ad storyboard. "
        "Each shot must have: type, duration (seconds), camera, context, focus, and optional caption or overlay for CTA. "
        "Reply with JSON only."
    )


    # 1. GENERATE DRAFT
    print("--- [PLANNER] Generating DRAFT storyboard...")
    draft_content = chat(
        [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.4, # Slightly higher temp for creativity in draft
    )
    
    if not draft_content or not draft_content.strip():
        print("Empty content from LLM (Draft), falling back to mock.")
        return _get_mock_storyboard(max_scenes)

    # 2. CRITIQUE DRAFT (Self-Correction)
    print("--- [PLANNER] Critiquing storyboard...")
    critique = _critique_storyboard(draft_content, product_description)
    print(f"--- [PLANNER] Critique received: {critique[:100]}...")

    # 3. REFINE STORYBOARD
    print("--- [PLANNER] Refining storyboard based on critique...")
    final_content = _refine_storyboard(draft_content, critique, product_description, max_scenes)
    
    # Extract JSON from the FINAL content
    json_str = _extract_json_block(final_content)
    
    # Debug logging
    print("FINAL LLM CONTENT:", final_content)

    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {e}. Content snippet: {json_str[:200]}")
        # Fallback on JSON error (e.g. truncated output)
        print("Falling back to mock storyboard due to JSON error.")
        return _get_mock_storyboard(max_scenes)

def _get_mock_storyboard(max_scenes: int) -> Dict[str, Any]:
    return {
        "shots": [
            {
                "type": "Wide shot",
                "duration": 5,
                "camera": "Static",
                "context": "Professional studio lighting",
                "focus": "Product centerpiece",
                "caption": "Experience perfection."
            },
            {
                "type": "Close-up",
                "duration": 5,
                "camera": "Slow pan",
                "context": "Detailed texture view",
                "focus": "Intricate details",
                "caption": "Crafted with care."
            }
        ][:max_scenes]
    }

