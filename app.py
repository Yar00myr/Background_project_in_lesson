import os
import time
import uuid
from fastapi import FastAPI, UploadFile, BackgroundTasks, HTTPException
import uvicorn

app = FastAPI()

UPLOAD_FOLDER = "saved_files/"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

tasks_status = {}

MAX_FILE_SIZE = 10 * 1024 * 1024


def save_file(file: UploadFile, file_path: str):
    with open(file_path, "wb") as f:
        chunk = file.file.read(1024 * 1024)
        while chunk:
            f.write(chunk)
            chunk = file.file.read(1024 * 1024)


def process_file(task_id: str, file_path: str):
    try:
        tasks_status[task_id] = {"status": "processing"}

        if not file_path.endswith((".txt", ".csv")):
            raise ValueError("Unsupported file format")

        with open(file_path, "r") as f:
            data = f.readlines()

        result = sum(len(line) for line in data)
        time.sleep(5)

        result_file = file_path + "_result.txt"
        with open(result_file, "w") as f:
            f.write(f"File processed. Total characters: {result}\n")

        tasks_status[task_id] = {"status": "completed", "result_file": result_file}
    except Exception as e:
        tasks_status[task_id] = {"status": "failed", "error": str(e)}


@app.post("/upload/")
async def upload_file(file: UploadFile, background_tasks: BackgroundTasks):
    content_length = int(file.headers.get("Content-Length", 0))
    if content_length > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File is too large")

    task_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)

    save_file(file, file_path)
    background_tasks.add_task(process_file, task_id, file_path)

    tasks_status[task_id] = {"status": "queued"}

    return {
        "task_id": task_id,
        "message": "File uploaded successfully, processing started.",
    }


def main():
    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
