from fastapi import FastAPI, HTTPException,  File, UploadFile, Form
from pydantic import BaseModel
import asyncio
import zipfile
import os
from io import BytesIO
from typing import List, Optional
from integration_src import MultiAgentIntegration
from config import api_config
from prompts import message_topic
from fastapi import BackgroundTasks

app = FastAPI()

integration_ai = MultiAgentIntegration()

background_task = None

async def upload_config_file(file: UploadFile = File(...)):
    file_location = os.path.join(api_config.UPLOAD_DIRECTORY, file.filename)
    
    with open(file_location, "wb") as f:
        content = await file.read()
        f.write(content)

    return file_location

def extract_zip_from_upload(uploaded_file: UploadFile, extract_to: str):

    try:
        file_bytes = BytesIO(uploaded_file.file.read())

        with zipfile.ZipFile(file_bytes, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
            print(f"Files extracted to: {extract_to}")
    except zipfile.BadZipFile:
        print("Error: The uploaded file is not a valid ZIP archive.")
    except Exception as e:
        print(f"Archive error occurred: {e}")

@app.post("/set_sessions_file")
async def set_sessions_file(
    sessions_file: UploadFile = File(...)
    ):
    if sessions_file is not None:
        sessions_path = await upload_config_file(file=sessions_file)
        api_config.set_sessions_path(file_path=sessions_path)
        print("Sessions file received:", sessions_file.filename)
    return {"message": f"Sessions config saved to path {api_config.SESSIONS_CONFIG_PATH}"}


@app.post("/set_agents_file")
async def set_agents_file(
    agents_file: UploadFile = File(...)
    ):
    if agents_file is not None:
        agents_path = await upload_config_file(file=agents_file)
        api_config.set_agents_path(file_path=agents_path)
        print("Agents file received:", agents_file.filename)
    return {"message": f"Agents config saved to path {api_config.AGENTS_CONFIG_PATH}"}

@app.post("/set_groups_file")
async def set_groups_file(
    group_file: UploadFile = File(...)
    ):
    if group_file is not None:
        group_path = await upload_config_file(file=group_file)
        api_config.set_groups_path(file_path=group_path)
        print("Group file received:", group_file.filename)
    return {"message": f"Groups config saved to path {api_config.GROUPS_CONFIG_PATH}"}

@app.post("/set_push_files")
async def set_push_files(
    push_archive: UploadFile = File(...)
    ):
    extract_to = api_config.PUSH_DIRECTORY
    
    if not os.path.exists(extract_to):
        os.makedirs(extract_to)

    extract_zip_from_upload(push_archive, extract_to)
    return {"message": f"File '{push_archive.filename}' extracted successfully to {extract_to}"}

@app.post("/set_config")
async def set_config(
    telegram_api_id: Optional[str] = None,
    telegram_api_hash: Optional[str] = None,
    open_ai_api_key: Optional[str] = None,
    open_ai_model: Optional[str] = None,
):
    if telegram_api_id is not None and telegram_api_hash is not None:
        api_config.set_telegram_api_options(api_id=telegram_api_id, api_hash=telegram_api_hash)
        print("Telegram API ID and Hash received:", telegram_api_id, telegram_api_hash)

    if open_ai_api_key is not None:
        api_config.set_openai_api_key(api_key=open_ai_api_key)
        print("OpenAI API Key received:", open_ai_api_key)

    if open_ai_model is not None:
        api_config.change_ai_model()
        print("OpenAI Model received:", open_ai_model)

    return api_config.get_all_data()

@app.post("/set_conversation_topic")
async def set_conversation_topic(
    topic: Optional[str] = None
    ):
    if topic is not None:
        message_topic.set_info_topic(message=topic)
    return {"message": f"Your conversation topic: {topic}"}

@app.post("/load_config_files")
async def load_config_files():
    try:
        await integration_ai.update_config_files()

        return {"message": f"Groups and sessions files updated"}
    except Exception as e:
        return {"error": f"Error for updating files: {e}"}

@app.post("/start_group_agents")
async def start_group_agents(
    group_id: Optional[int] = None
    ):
    try:
        if group_id is not None:
            await integration_ai.start_agents_for_group(group_id=group_id)
        return {"message": f"Simulation started for group with id {group_id}"}
    except Exception as e:
        return {"error": f"Simulation start for {group_id} group failed with: {e}"}


@app.post("/stop_group_agents")
async def stop_group_agents(
    group_id: Optional[int] = None
    ):
    try:
        if group_id is not None:
            await integration_ai.stop_group_sessions(group_id=group_id)
        return {"message": f"Simulation stopped for group with id {group_id}"}
    except Exception as e:
        return {"error": f"Simulation stop for {group_id} group failed with: {e}"}
    
@app.post("/start_agents")
async def start_agents(background_tasks: BackgroundTasks):
    global background_task

    try:
        #await integration_ai.update_config_files()
        background_task = asyncio.create_task(integration_ai.start_agents())
        
        return {"message": "Agents simulation started in background."}
    except Exception as e:
        return {"error": f"Failed to start agents simulation: {e}"}
    
@app.get("/agents_status")
async def agents_status():
    global background_task

    if background_task is None:
        return {"status": "No task running"}
    
    if background_task.done():
        return {"status": "Task completed"}
    
    return {"status": "Task is running"}

@app.post("/stop_agents")
async def stop_agents():
    try:
        await integration_ai.stop_all_sessions()

        return {"message": f"Simulation stopped for all agents"}
    except Exception as e:
        return {"error": f"Simulation stop failed with: {e}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)