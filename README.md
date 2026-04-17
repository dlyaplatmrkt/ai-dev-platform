# AI Dev Platform

Self-hosted AI coding platform: generate websites, bots and APIs with local LLM, preview projects and push to GitHub — all from one web interface.

## Features
- Generate full projects (website, landing, REST API, Telegram bot) with local AI
- Live preview of generated projects
- One-click GitHub push
- Index your own repos for AI context
- 100% local, no cloud API keys needed

## Stack
- **Backend**: Python + FastAPI
- **Frontend**: HTML + CSS + JavaScript
- **AI**: Ollama (qwen2.5-coder:7b or any model)
- **Embeddings**: nomic-embed-text

## Quick Start (recommended)

### 1. Prerequisites
- [Ollama](https://ollama.ai) installed and running
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed
- Git installed

### 2. Pull models
```bash
ollama pull qwen2.5-coder:7b
ollama pull nomic-embed-text
```

### 3. Clone and run
```bash
git clone https://github.com/dlyaplatmrkt/ai-dev-platform.git
cd ai-dev-platform
docker-compose up --build
```

### 4. Open in browser
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## Manual Start (without Docker)

### 1. Start Ollama
```bash
ollama serve
```

### 2. Start Backend
```bash
cd backend
pip install -r requirements.txt
cp ../.env.example .env
python main.py
```

### 3. Open Frontend
Open `frontend/index.html` in your browser, or serve with:
```bash
cd frontend
python -m http.server 3000
```
Then open http://localhost:3000

---

## Usage

1. **Generate** — Enter a project name, choose a template (Website / Landing / API / Bot), describe what to build, click Generate.
2. **Preview** — After generation, click Preview to run the project locally and see it in an iframe.
3. **GitHub Push** — Go to GitHub Push tab, enter your repo URL and GitHub token (Personal Access Token), click Push.
4. **Index Repo** — Paste any GitHub repo URL to index it, so the AI can use it as context for future generations.

---

## Project Structure
```
ai-dev-platform/
  backend/
    main.py          # FastAPI app
    agent.py         # LLM agent (Ollama)
    github_service.py # Git + GitHub push
    workspace.py     # Project file management + preview
    indexer.py       # Repo indexer (embeddings)
    requirements.txt
    Dockerfile
  frontend/
    index.html       # Main UI
    style.css        # Dark theme styles
    app.js           # Frontend logic
  docker-compose.yml
  .env.example
```

## Environment Variables
See `.env.example` for all available settings.

| Variable | Default | Description |
|---|---|---|
| OLLAMA_URL | http://localhost:11434 | Ollama API URL |
| OLLAMA_MODEL | qwen2.5-coder:7b | Model for code generation |
| EMBED_MODEL | nomic-embed-text | Model for embeddings |
| WORKSPACE_DIR | ./workspace | Where projects are saved |
| INDEX_DIR | ./index | Where embeddings are saved |
