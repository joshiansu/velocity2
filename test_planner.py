
import sys
import os
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO, stream=sys.stdout)

# Add project root to sys.path
sys.path.append(os.getcwd())

from backend.agents.planner import plan_storyboard

if __name__ == "__main__":
    description = "A sleek, cyber-punk style energy drink called 'Neon Boost' glowing in the dark."
    print(f"Testing planner with description: {description}")
    
    storyboard = plan_storyboard(description, max_scenes=3)
    
    print("\n--- FINAL STORYBOARD JSON ---")
    print(json.dumps(storyboard, indent=2))
