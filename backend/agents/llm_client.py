import requests
import logging
import json
from typing import List, Dict, Any

# Configure logging
logger = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "phi3"  # or "llama3.1"

def chat(messages: List[Dict[str, str]], temperature: float = 0.3) -> str:
    """
    Thin wrapper around Ollama chat API.
    messages: [{"role": "system"/"user"/"assistant", "content": "..."}]
    
    Falls back to a mock response if Ollama is unreachable.
    """
    logger.info(f"Sending request to Ollama ({MODEL_NAME}): {messages[-1]['content'][:50]}...")
    
    payload: Dict[str, Any] = {
        "model": MODEL_NAME,
        "messages": messages,
        "options": {
            "temperature": temperature,
        },
        "stream": False,
    }
    
    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        content = data["message"]["content"]
        logger.info("Received response from Ollama.")
        return content
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
        logger.warning(f"Failed to connect to Ollama: {e}. Returning MOCK response.")
        
        # Determine if this is a storyboard request based on system prompt
        is_storyboard = any("storyboard" in m.get("content", "").lower() for m in messages if m.get("role") == "system")
        
        if is_storyboard:
            return json.dumps({
                "shots": [
                    {
                        "type": "Wide shot",
                        "duration": 5,
                        "camera": "Static",
                        "context": "A bright, clean studio setting",
                        "focus": "The product in the center",
                        "caption": "Introducing the new standard."
                    },
                    {
                        "type": "Close-up",
                        "duration": 5,
                        "camera": "Slow zoom in",
                        "context": "Detailed view of the product texture",
                        "focus": "Product features",
                        "caption": "Unmatched quality."
                    },
                    {
                        "type": "Medium shot",
                        "duration": 5,
                        "camera": "Pan left",
                        "context": "Lifestyle setting with soft lighting",
                        "focus": "Product in use",
                        "caption": "Designed for you."
                    },
                    {
                        "type": "Wide shot",
                        "duration": 5,
                        "camera": "Static",
                        "context": "Product with logo overlay",
                        "focus": "Brand identity",
                        "overlay": "Shop Now"
                    }
                ]
            })
        else:
            return "This is a mock response from Velocity2 because Ollama is offline."
            
    except Exception as e:
        logger.error(f"Unexpected error in LLM client: {e}")
        raise

