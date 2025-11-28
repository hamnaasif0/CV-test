from fastapi import FastAPI, File, UploadFile, Form
import uuid
import requests

app = FastAPI()

# This is updated automatically by Colab
COLAB_WEBHOOK_URL = None

# In-memory store for results
jobs = {}

@app.post("/process")
async def process_image(file: UploadFile = File(...)):
    global COLAB_WEBHOOK_URL

    if COLAB_WEBHOOK_URL is None:
        return {"error": "Colab ngrok URL not registered yet!"}

    job_id = str(uuid.uuid4())
    image_bytes = await file.read()

    # Store initial status
    jobs[job_id] = {"status": "processing", "model_url": None}

    # Send image to Colab
    requests.post(
        COLAB_WEBHOOK_URL,
        files={"file": ("input.png", image_bytes, "image/png")},
        data={"job_id": job_id}
    )

    return {"job_id": job_id}


# ⭐ This endpoint is called by Colab ONCE after ngrok starts
@app.post("/update-ngrok")
async def update_ngrok(url: str = Form(...)):
    global COLAB_WEBHOOK_URL
    COLAB_WEBHOOK_URL = url
    print("Updated NGROK URL:", COLAB_WEBHOOK_URL)
    return {"status": "ok", "ngrok_url": COLAB_WEBHOOK_URL}


# ⭐ This endpoint receives final model URL from Colab
@app.post("/callback")
async def callback(job_id: str = Form(...), model_url: str = Form(...)):
    if job_id not in jobs:
        jobs[job_id] = {}

    jobs[job_id]["status"] = "done"
    jobs[job_id]["model_url"] = model_url

    print("Job completed:", job_id, model_url)
    return {"received": True}


# Unity will poll this endpoint
@app.get("/status/{job_id}")
async def get_status(job_id: str):
    if job_id not in jobs:
        return {"error": "job not found"}

    return jobs[job_id]
