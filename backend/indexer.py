import os
import json
import httpx
from pathlib import Path
from typing import List, Dict, Optional

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")
INDEX_DIR = os.getenv("INDEX_DIR", "./index")


class Indexer:
    def __init__(self):
        self.index_path = Path(INDEX_DIR)
        self.index_path.mkdir(parents=True, exist_ok=True)

    async def index(self, repo_url: str, token: Optional[str] = None) -> dict:
        import subprocess
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            clone_url = repo_url
            if token and repo_url.startswith("https://"):
                clone_url = repo_url.replace("https://", f"https://{token}@")

            result = subprocess.run(
                ["git", "clone", "--depth", "1", clone_url, tmpdir],
                capture_output=True, text=True
            )

            if result.returncode != 0:
                return {"status": "error", "message": result.stderr}

            files = self._collect_files(tmpdir)
            chunks = self._chunk_files(files)
            embeddings = await self._embed_chunks(chunks)
            self._save_index(repo_url, chunks, embeddings)

        return {"status": "ok", "indexed": len(chunks)}

    def _collect_files(self, directory: str) -> List[Dict]:
        files = []
        extensions = {".py", ".js", ".ts", ".html", ".css", ".md", ".json", ".yaml", ".yml"}
        for f in Path(directory).rglob("*"):
            if f.is_file() and f.suffix in extensions:
                try:
                    content = f.read_text(encoding="utf-8")
                    files.append({"path": str(f), "content": content})
                except Exception:
                    pass
        return files

    def _chunk_files(self, files: List[Dict], chunk_size: int = 1000) -> List[Dict]:
        chunks = []
        for file in files:
            content = file["content"]
            for i in range(0, len(content), chunk_size):
                chunks.append({
                    "path": file["path"],
                    "content": content[i:i + chunk_size],
                    "offset": i
                })
        return chunks

    async def _embed_chunks(self, chunks: List[Dict]) -> List[List[float]]:
        embeddings = []
        async with httpx.AsyncClient(timeout=60) as client:
            for chunk in chunks:
                try:
                    response = await client.post(
                        f"{OLLAMA_URL}/api/embeddings",
                        json={"model": EMBED_MODEL, "prompt": chunk["content"]}
                    )
                    data = response.json()
                    embeddings.append(data.get("embedding", []))
                except Exception:
                    embeddings.append([])
        return embeddings

    def _save_index(self, repo_url: str, chunks: List[Dict], embeddings: List[List[float]]) -> None:
        safe_name = repo_url.replace("/", "_").replace(":", "_")
        index_file = self.index_path / f"{safe_name}.json"
        data = [{"chunk": c, "embedding": e} for c, e in zip(chunks, embeddings)]
        index_file.write_text(json.dumps(data), encoding="utf-8")

    def search(self, query_embedding: List[float], repo_url: str, top_k: int = 5) -> List[Dict]:
        import math

        safe_name = repo_url.replace("/", "_").replace(":", "_")
        index_file = self.index_path / f"{safe_name}.json"

        if not index_file.exists():
            return []

        data = json.loads(index_file.read_text())

        def cosine_similarity(a, b):
            if not a or not b:
                return 0.0
            dot = sum(x * y for x, y in zip(a, b))
            norm_a = math.sqrt(sum(x ** 2 for x in a))
            norm_b = math.sqrt(sum(x ** 2 for x in b))
            return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0

        scored = [
            (cosine_similarity(query_embedding, item["embedding"]), item["chunk"])
            for item in data
        ]
        scored.sort(key=lambda x: x[0], reverse=True)
        return [chunk for _, chunk in scored[:top_k]]
