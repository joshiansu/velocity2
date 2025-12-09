# backend/test/quick_test_grok.py
import os
import sys

# add project root (one level up from backend) to sys.path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT)

from backend.agents.planner import plan_storyboard

if __name__ == "__main__":
    print(plan_storyboard("Matte black insulated water bottle with logo", max_scenes=4))
