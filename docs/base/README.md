# Hybrid RAG documentation

This folder contains the full README content split into smaller local Markdown files.

## Reading order

- [Overview and included system pieces](./01-overview.md)
- [Architecture, layers, and main components](./02-architecture.md)
- [Local setup and first end-to-end run](./03-quickstart.md)
- [BM25, dense MiniLM, and hybrid retrieval](./04-retrieval-modes.md)
- [Prompt grounding, citations, and validation](./05-rag-and-citations.md)
- [Evaluation runners, metrics, and order of experiments](./06-experiments.md)
- [Frontend workflow and UI debugging](./07-web-playground.md)
- [FastAPI endpoints and request/response examples](./08-api.md)
- [Expected outputs and run context](./09-results-and-artifacts.md)
- [YAML configuration files](./10-configuration.md)
- [Common runtime and evaluation issues](./11-troubleshooting.md)
- [Planned improvements](./12-roadmap.md)

## Local port map

```text
Weaviate REST  = 18080
Weaviate gRPC  = 15051
FastAPI        = 8080
Frontend       = 5173
```

Return to the repository root README: [../../README.md](../../README.md)
