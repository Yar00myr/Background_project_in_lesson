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

    except ValueError as ve:

        tasks_status[task_id] = {
            "status": "failed",
            "error_type": "ValueError",
            "error_message": str(ve),
        }
    except FileNotFoundError as fnfe:

        tasks_status[task_id] = {
            "status": "failed",
            "error_type": "FileNotFoundError",
            "error_message": f"File not found: {str(fnfe)}",
        }
    except Exception as e:

        tasks_status[task_id] = {
            "status": "failed",
            "error_type": "GeneralError",
            "error_message": str(e),
        }


@app.post("/upload/")
async def upload_file(file: UploadFile, background_tasks: BackgroundTasks):
    content_length = int(file.headers.get("Content-Length", 0))
    if content_length > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File is too large")

    task_id = str(uuid.uuid4())
    path_for_file = os.path.join(UPLOAD_FOLDER, file.filename)

    save_file(file, path_for_file)
    background_tasks.add_task(
    process_file, 
    task_id, path_for_file
    )

    tasks_status[task_id] = {"status": "queued"}

    return {
        "task_id": task_id,
        "message": "File uploaded successfully, processing started.",
    }


@app.get("/status/{task_id}")
def get_task_status(task_id: str):
    task_info = tasks_status.get(task_id)

    if task_info is None:
        raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")

    return {"task_id": task_id, "status": task_info}


def main():
    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
