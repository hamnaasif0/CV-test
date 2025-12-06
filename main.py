from fastapi import FastAPI, File, UploadFile, Form
import uuid
import requests
import os
from fastapi.responses import FileResponse

app = FastAPI()

# Updated by Colab using /update-ngrok
COLAB_WEBHOOK_URL = None

# Store job statuses + mesh paths
jobs = {}

# Folder to store downloaded mesh files
MESH_FOLDER = "/app/meshes"
os.makedirs(MESH_FOLDER, exist_ok=True)


# ---------------------------------------------------------
# 1️⃣ UNITY → RAILWAY (Upload Image)
# ---------------------------------------------------------
@app.post("/process")
async def process_image(file: UploadFile = File(...)):
    global COLAB_WEBHOOK_URL

    if COLAB_WEBHOOK_URL is None:
        return {"error": "Colab ngrok URL not registered yet!"}

    job_id = str(uuid.uuid4())
    image_bytes = await file.read()

    # Initialize job state
    jobs[job_id] = {
        "status": "processing",
        "mesh_path": None
    }

    # Forward to Colab
    requests.post(
        COLAB_WEBHOOK_URL,
        files={"file": ("input.png", image_bytes, "image/png")},
        data={"job_id": job_id}
    )

    return {"job_id": job_id}



# ---------------------------------------------------------
# 2️⃣ COLAB → RAILWAY (Send NGROK URL)
# ---------------------------------------------------------
@app.post("/update-ngrok")
async def update_ngrok(url: str = Form(...)):
    global COLAB_WEBHOOK_URL
    COLAB_WEBHOOK_URL = url
    print("Updated NGROK URL:", COLAB_WEBHOOK_URL)
    return {"status": "ok"}



# ---------------------------------------------------------
# 3️⃣ COLAB → RAILWAY (Send mesh.obj directly)
# ---------------------------------------------------------
@app.post("/callback")
async def callback(
    job_id: str = Form(...),
    file: UploadFile = File(...)
):
    if job_id not in jobs:
        jobs[job_id] = {}

    # Save the mesh file
    mesh_path = os.path.join(MESH_FOLDER, f"{job_id}.obj")
    with open(mesh_path, "wb") as f:
        f.write(await file.read())

    jobs[job_id]["status"] = "done"
    jobs[job_id]["mesh_path"] = mesh_path

    print(f"✔ Mesh saved for job {job_id}: {mesh_path}")

    return {"received": True}



# ---------------------------------------------------------
# 4️⃣ UNITY → RAILWAY (Check status)
# ---------------------------------------------------------
@app.get("/status/{job_id}")
async def get_status(job_id: str):
    if job_id not in jobs:
        return {"error": "job not found"}

    return {
        "status": jobs[job_id]["status"]
    }



# ---------------------------------------------------------
# 5️⃣ UNITY → RAILWAY (Download final mesh.obj)
# ---------------------------------------------------------
@app.get("/mesh/{job_id}")
async def download_mesh(job_id: str):

    if job_id not in jobs:
        return {"error": "job not found"}

    mesh_path = jobs[job_id]["mesh_path"]

    if mesh_path is None:
        return {"error": "mesh not ready"}

    # Return mesh.obj as file
    return FileResponse(mesh_path, media_type="application/octet-stream", filename="model.obj")