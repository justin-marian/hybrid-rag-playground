# Setup & dependencies

Quick reference for installing everything needed by the project. 
The authoritative source is `pyproject.toml`; this file just summarises the steps.

## 1. System dependencies

- Python 3.10+: `python3 --version`
- Docker + Docker Compose v2: `docker compose version`
- Ollama: installed natively on the host (not in a container)
- ~10 GB free disk for BEIR + Weaviate volume + embedding cache

## 2. Python virtual environment

```bash
python -m venv .venv
source .venv/bin/activate           # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -e ".[dev]"
```

The `[dev]` extra includes `ruff`, `pre-commit`, and `pytest`.

## 3. Ollama models

```bash
ollama serve                        # background service (skip if already running)
ollama pull gemma2:2b               # default (~ 1.6 GB)
ollama pull llama3.2:3b             # optional, only with 16+ GB RAM (~ 2 GB)
```

## 4. Pre-commit (optional)

```bash
pre-commit install
```

## 5. Sanity check

```bash
python -c "import beir, weaviate, sentence_transformers, ollama; print('ok')"
docker compose -f docker/docker-compose.yml up -d
curl -s http://localhost:8080/v1/.well-known/ready && echo " ✓ Weaviate ready"
curl -s http://localhost:11434/api/tags     # Ollama should respond
```
