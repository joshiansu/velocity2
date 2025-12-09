# backend/api/main.py
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.agents.planner import extract_product_attributes, plan_storyboard

app = FastAPI(title="Agentic Video Ads - Storyboard API")

# optional CORS if you later add a Next.js UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# @app.post("/generate/storyboard")
# async def generate_storyboard(
#     image: UploadFile = File(...),
#     max_scenes: int = 4,
# ):
#     try:
#         image_bytes = await image.read()
#         if not image_bytes:
#             raise HTTPException(status_code=400, detail="Empty image upload")

#         product_desc = extract_product_attributes(image_bytes)
#         storyboard = plan_storyboard(product_desc, max_scenes=max_scenes)

#         return {
#             "product_description": product_desc,
#             "storyboard": storyboard,
#         }
#     except Exception as e:
#         # Simple error surface for now; you can log e with struct logging
#         raise HTTPException(status_code=500, detail=str(e))
# backend/api/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
class StoryboardRequest(BaseModel):
    product_description: str
    max_scenes: int = 4

from backend.agents.planner import (
    extract_product_attributes_from_text,
    plan_storyboard,
)

@app.post("/generate/storyboard")
async def generate_storyboard(body: StoryboardRequest):
    # try:
        # print(plan_storyboard("Matte black insulated water bottle with logo", max_scenes=4))

    product_desc = extract_product_attributes_from_text(body.product_description)
    storyboard = plan_storyboard(product_desc, max_scenes=body.max_scenes)
    
    return {
        "product_description": product_desc,
        "storyboard": storyboard,
    }
    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=str(e))


from backend.agents.planner import plan_storyboard
from backend.pipelines.video_pipeline import generate_video_from_storyboard

class VideoRequest(BaseModel):
    product_description: str
    max_scenes: int = 4


@app.post("/generate/video")
async def generate_video(body: VideoRequest):
    storyboard = plan_storyboard(body.product_description, max_scenes=body.max_scenes)
    print(type(storyboard))
    result = generate_video_from_storyboard(storyboard, body.product_description)
    return {
        "product_description": body.product_description,
        "storyboard": storyboard,
        "job": result,
    }
