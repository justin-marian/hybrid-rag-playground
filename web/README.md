# Web UI

Tiny single-page app built with **Vite + React + TypeScript**, served by **Bun**,
that talks to the FastAPI backend (`app.py` in the repo root).

## Features

- Pick any indexed BEIR dataset, retriever (BM25 / Dense / Hybrid), top-k and α.
- **Retrieve** mode: see the ranked hits, scores, and chunk metadata.
- **RAG** mode: get a cited LLM answer with inline `[chunk_id]` chips. Invented
  citations are flagged in red. Hits that the LLM actually cited are highlighted.
- Live API health pill in the header.
- The full prompt sent to the LLM is one click away (handy for the report).

## Prerequisites

- [Bun](https://bun.sh/) ≥ 1.1
- The backend running (`uvicorn app:app` in the repo root)
- Weaviate + Ollama running (see the top-level README)

## Develop

```bash
cd web
bun install
bun run dev
```

Open <http://localhost:5173>. The dev server proxies `/api/*` to
`http://localhost:8080` (configurable via `web/.env`).

## Type-check & build

```bash
bun run typecheck
bun run build       # outputs to web/dist
bun run preview     # serve the built bundle locally
```

## Production

`bun run build` produces a static bundle in `dist/`. Serve it with any static
host (or behind the FastAPI itself, if you want to mount it later). For the
homework, running it via `bun run dev` alongside `uvicorn` is enough.
