from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional
import uvicorn
import json
import os

from agent import Agent
from github_service import GitHubService
from workspace import Workspace
from indexer import Indexer

app = FastAPI(title="AI Dev Platform", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = Agent()
github = GitHubService()
workspace = Workspace()
indexer = Indexer()


class TaskRequest(BaseModel):
    task: str
    project_name: str
    template: Optional[str] = "website"


class GitHubPushRequest(BaseModel):
    project_name: str
    commit_message: str
    repo_url: str
    token: str


class IndexRequest(BaseModel):
    repo_url: str
    token: Optional[str] = None


@app.get("/")
async def root():
    with open("../frontend/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())


@app.post("/api/generate")
async def generate_project(req: TaskRequest):
    result = await agent.generate(req.task, req.project_name, req.template)
    return {"status": "ok", "files": result["files"], "plan": result["plan"]}


@app.get("/api/projects")
async def list_projects():
    projects = workspace.list_projects()
    return {"projects": projects}


@app.get("/api/projects/{project_name}/files")
async def get_project_files(project_name: str):
    files = workspace.get_files(project_name)
    return {"files": files}


@app.get("/api/projects/{project_name}/preview")
async def preview_project(project_name: str):
    url = workspace.start_preview(project_name)
    return {"preview_url": url}


@app.post("/api/projects/{project_name}/stop")
async def stop_preview(project_name: str):
    workspace.stop_preview(project_name)
    return {"status": "stopped"}


@app.post("/api/github/push")
async def push_to_github(req: GitHubPushRequest):
    result = github.push(
        req.project_name,
        req.commit_message,
        req.repo_url,
        req.token
    )
    return result


@app.post("/api/index")
async def index_repo(req: IndexRequest):
    result = await indexer.index(req.repo_url, req.token)
    return result


@app.websocket("/ws/generate")
async def websocket_generate(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            async for chunk in agent.stream_generate(
                payload["task"],
                payload["project_name"],
                payload.get("template", "website")
            ):
                await websocket.send_text(json.dumps(chunk))
    except WebSocketDisconnect:
        pass


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
