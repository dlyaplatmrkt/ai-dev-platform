import os
import json
import httpx
from typing import AsyncGenerator

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")

TEMPLATES = {
    "website": "Create a modern responsive website with HTML, CSS and JavaScript.",
    "bot": "Create a Python Telegram bot using python-telegram-bot library.",
    "api": "Create a REST API using FastAPI with proper endpoints and models.",
    "landing": "Create a beautiful landing page with HTML, CSS animations and JS.",
}


class Agent:
    def __init__(self):
        self.model = DEFAULT_MODEL
        self.base_url = OLLAMA_URL

    def _build_prompt(self, task: str, template: str) -> str:
        template_hint = TEMPLATES.get(template, "")
        return f"""You are an expert software developer. Your job is to generate complete, working project files.

{template_hint}

Task: {task}

Respond ONLY with a JSON object in this exact format:
{{
  "plan": "Brief description of what you will create",
  "files": [
    {{
      "path": "relative/path/to/file.ext",
      "content": "full file content here"
    }}
  ]
}}

Generate ALL necessary files for a complete, working project. Do not omit any files."""

    async def generate(self, task: str, project_name: str, template: str = "website") -> dict:
        prompt = self._build_prompt(task, template)
        async with httpx.AsyncClient(timeout=300) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                }
            )
            data = response.json()
            raw = data.get("response", "{}")
            try:
                result = json.loads(raw)
            except json.JSONDecodeError:
                result = {"plan": "Generated project", "files": []}

            from workspace import Workspace
            ws = Workspace()
            ws.save_project(project_name, result.get("files", []))

            return result

    async def stream_generate(
        self,
        task: str,
        project_name: str,
        template: str = "website"
    ) -> AsyncGenerator[dict, None]:
        prompt = self._build_prompt(task, template)
        buffer = ""

        async with httpx.AsyncClient(timeout=300) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": True
                }
            ) as response:
                async for line in response.aiter_lines():
                    if line:
                        try:
                            chunk = json.loads(line)
                            token = chunk.get("response", "")
                            buffer += token
                            yield {"type": "token", "content": token}
                            if chunk.get("done"):
                                try:
                                    result = json.loads(buffer)
                                    from workspace import Workspace
                                    ws = Workspace()
                                    ws.save_project(project_name, result.get("files", []))
                                    yield {"type": "done", "result": result}
                                except json.JSONDecodeError:
                                    yield {"type": "error", "message": "Failed to parse response"}
                        except json.JSONDecodeError:
                            pass
