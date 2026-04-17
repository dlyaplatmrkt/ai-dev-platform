import os
import json
import subprocess
import threading
from pathlib import Path
from typing import List, Dict

WORKSPACE_DIR = os.getenv("WORKSPACE_DIR", "./workspace")

_preview_processes: Dict[str, subprocess.Popen] = {}
_preview_ports: Dict[str, int] = {}
_port_counter = [8100]
_lock = threading.Lock()


class Workspace:
    def __init__(self):
        self.base = Path(WORKSPACE_DIR)
        self.base.mkdir(parents=True, exist_ok=True)

    def save_project(self, project_name: str, files: List[Dict]) -> None:
        project_path = self.base / project_name
        project_path.mkdir(parents=True, exist_ok=True)

        for file_info in files:
            file_path = project_path / file_info["path"]
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(file_info["content"], encoding="utf-8")

        meta = {"name": project_name, "files": [f["path"] for f in files]}
        (project_path / ".meta.json").write_text(json.dumps(meta), encoding="utf-8")

    def list_projects(self) -> List[Dict]:
        projects = []
        for d in self.base.iterdir():
            if d.is_dir():
                meta_file = d / ".meta.json"
                if meta_file.exists():
                    meta = json.loads(meta_file.read_text())
                    projects.append(meta)
                else:
                    projects.append({"name": d.name, "files": []})
        return projects

    def get_files(self, project_name: str) -> List[Dict]:
        project_path = self.base / project_name
        if not project_path.exists():
            return []
        files = []
        for f in project_path.rglob("*"):
            if f.is_file() and not f.name.startswith("."):
                try:
                    content = f.read_text(encoding="utf-8")
                except Exception:
                    content = "<binary file>"
                files.append({
                    "path": str(f.relative_to(project_path)),
                    "content": content
                })
        return files

    def start_preview(self, project_name: str) -> str:
        with _lock:
            if project_name in _preview_processes:
                port = _preview_ports[project_name]
                return f"http://localhost:{port}"

            port = _port_counter[0]
            _port_counter[0] += 1

        project_path = self.base / project_name

        # Check if it's a Python/Flask project
        if (project_path / "app.py").exists():
            proc = subprocess.Popen(
                ["python", "app.py"],
                cwd=str(project_path),
                env={**os.environ, "PORT": str(port), "FLASK_RUN_PORT": str(port)}
            )
        else:
            # Static HTML preview with Python http.server
            proc = subprocess.Popen(
                ["python", "-m", "http.server", str(port)],
                cwd=str(project_path)
            )

        with _lock:
            _preview_processes[project_name] = proc
            _preview_ports[project_name] = port

        return f"http://localhost:{port}"

    def stop_preview(self, project_name: str) -> None:
        with _lock:
            proc = _preview_processes.pop(project_name, None)
            _preview_ports.pop(project_name, None)
        if proc:
            proc.terminate()
