from fastapi import FastAPI, File, UploadFile, Form
import uuid
import requests

app = FastAPI()

# Change this later to the Colab webhook URL printed by ngrok
COLAB_WEBHOOK_URL = "https://your-colab-url.ngrok-free.app/webhook"

# In-memory store for results
jobs = {}

@app.post("/process")
async def process_image(file: UploadFile = File(...)):
    job_id = str(uuid.uuid4())
    image_bytes = await file.read()

    # Store initial status
    jobs[job_id] = {"status": "processing", "model_url": None}

    # Send to Google Colab
    requests.post(
        COLAB_WEBHOOK_URL,
        files={"file": ("input.png", image_bytes, "image/png")},
        data={"job_id": job_id}
    )

    return {"job_id": job_id}


@app.post("/callback")
async def callback(job_id: str = Form(...), model_url: str = Form(...)):
    """Google Colab calls this when the model is ready"""
    jobs[job_id] = {"status": "done", "model_url": model_url}
    return {"received": True}


@app.get("/status/{job_id}")
async def get_status(job_id: str):
    if job_id not in jobs:
        return {"error": "job not found"}

    return jobs[job_id]
