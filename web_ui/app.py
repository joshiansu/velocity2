import streamlit as st
import sys
import os
import json
import logging
from pathlib import Path

# Configure logging to show in console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


# Add project root to sys.path to allow imports from backend
# Assuming we run from project root, but this helps if running from within web_ui too
project_root = str(Path(__file__).parent.parent.resolve())
if project_root not in sys.path:
    sys.path.append(project_root)

# Import backend modules
try:
    from backend.agents.planner import plan_storyboard
    from backend.pipelines.video_pipeline import generate_video_from_storyboard
except ImportError as e:
    st.error(f"Failed to import backend modules: {e}")
    st.stop()

st.set_page_config(
    page_title="Velocity2 - Agentic Video Ads",
    page_icon="🎬",
    layout="wide"
)

def main():
    st.title("🎬 Velocity2: Agentic Video Ads")
    st.markdown("""
    Generate cinematic video ads from a simple product description using AI agents.
    """)

    # Sidebar for configuration
    with st.sidebar:
        st.header("Configuration")
        max_scenes = st.slider("Max Scenes", min_value=1, max_value=8, value=4)
        
        st.info("Currently using 'mock' provider for demo purposes.")

    # 1. Product Description Input (Top)
    with st.container():
        st.subheader("1. Describe your Product")
        product_description = st.text_area(
            "Enter product details",
            height=100,
            label_visibility="collapsed", # Cleaner look
            placeholder="e.g. A matte black insulated water bottle with a mountain logo, sitting on a rock near a stream."
        )

        if st.button("Generate Storyboard", type="primary"):
            if not product_description:
                st.warning("Please enter a product description first.")
            else:
                with st.spinner("🤖 Scene Agent is planning the storyboard..."):
                    try:
                        storyboard = plan_storyboard(product_description, max_scenes=max_scenes)
                        st.session_state['storyboard'] = storyboard
                        st.session_state['product_description'] = product_description
                        st.success("Storyboard generated!")
                    except Exception as e:
                        st.error(f"Error generating storyboard: {e}")

    # 2. Results Area (Below)
    if 'storyboard' in st.session_state:
        st.divider()
        st.subheader("2. Review & Generate Video")
        
        col_preview, col_json = st.columns([3, 2])
        
        storyboard = st.session_state['storyboard']
        shots = storyboard.get("shots", [])

        # Left Column: Visual Preview (Scrollable)
        with col_preview:
            st.markdown("### Scenes Preview")
            # Use fixed height container to avoid full page scroll
            with st.container(height=400):
                for i, shot in enumerate(shots):
                    st.markdown(f"**Scene {i+1}: {shot.get('type', 'Standard')} shot**")
                    st.text(f"Camera: {shot.get('camera', 'Static')}")
                    st.caption(shot.get("context", "") or shot.get("description", ""))
                    if shot.get("caption") or shot.get("overlay"):
                        st.code(f"Text: {shot.get('caption') or shot.get('overlay')}", language=None)
                    st.divider()
            
            # Generate Video Action
            if st.button("Generate Video", type="primary", use_container_width=True):
                with st.spinner("🎥 Compiling scenes and rendering video..."):
                    try:
                        result = generate_video_from_storyboard(
                            storyboard, 
                            st.session_state['product_description']
                        )
                        st.session_state['video_result'] = result
                        st.success("Video generated successfully!")
                    except Exception as e:
                        st.error(f"Error generating video: {e}")

        # Right Column: JSON & Final Video
        with col_json:
            with st.expander("Raw Storyboard JSON", expanded=False):
                st.json(storyboard)
            
            if 'video_result' in st.session_state:
                result = st.session_state['video_result']
                video_path = result.get('final_video_path')
                
                if video_path and os.path.exists(video_path):
                    st.success("Final Video")
                    st.video(video_path)
                    st.markdown(f"**Job ID:** `{result.get('job_id')}`")
                else:
                    st.error("Video file not found.")

if __name__ == "__main__":
    main()
