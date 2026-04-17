import os
import subprocess
import shutil
from pathlib import Path

WORKSPACE_DIR = os.getenv("WORKSPACE_DIR", "./workspace")


class GitHubService:
    def __init__(self):
        self.workspace = Path(WORKSPACE_DIR)

    def push(self, project_name: str, commit_message: str, repo_url: str, token: str) -> dict:
        project_path = self.workspace / project_name

        if not project_path.exists():
            return {"status": "error", "message": f"Project {project_name} not found"}

        try:
            git_dir = project_path / ".git"
            if not git_dir.exists():
                self._run(["git", "init"], cwd=project_path)
                self._run(["git", "branch", "-M", "main"], cwd=project_path)

            # Set remote with token
            if repo_url.startswith("https://"):
                auth_url = repo_url.replace("https://", f"https://{token}@")
            else:
                auth_url = repo_url

            remotes = self._run(["git", "remote"], cwd=project_path)
            if "origin" in remotes:
                self._run(["git", "remote", "set-url", "origin", auth_url], cwd=project_path)
            else:
                self._run(["git", "remote", "add", "origin", auth_url], cwd=project_path)

            self._run(["git", "config", "user.email", "ai-dev-platform@local"], cwd=project_path)
            self._run(["git", "config", "user.name", "AI Dev Platform"], cwd=project_path)
            self._run(["git", "add", "."], cwd=project_path)
            self._run(["git", "commit", "-m", commit_message], cwd=project_path)
            self._run(["git", "push", "-u", "origin", "main", "--force"], cwd=project_path)

            return {"status": "ok", "message": "Pushed to GitHub successfully"}

        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_diff(self, project_name: str) -> str:
        project_path = self.workspace / project_name
        if not project_path.exists():
            return ""
        try:
            return self._run(["git", "diff", "HEAD"], cwd=project_path)
        except Exception:
            return ""

    def _run(self, cmd: list, cwd: Path) -> str:
        result = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True
        )
        if result.returncode != 0 and result.stderr:
            # Allow commit to fail if nothing to commit
            if "nothing to commit" not in result.stderr:
                raise Exception(result.stderr)
        return result.stdout
