# Overview and included system pieces

[Index](./00-index.md) · [Index](./00-index.md) · [Next](./02-architecture.md)

---

## :sparkles: Overview

Hybrid RAG is a compact RAG system built for one practical reason: it lets you see what happened before the answer was generated.

Most RAG demos show the final response and hide the interesting parts. This project keeps the useful debugging signals visible: which chunks were retrieved, how they were scored, which document they came from, what prompt was sent to the model, which citations the model used, and whether those citations were actually available in the retrieved context.

The stack is local by default:

- Weaviate stores chunked documents and serves BM25, dense, and hybrid retrieval.
- MiniLM embeddings provide the dense retrieval signal.
- Ollama runs the generation model locally.
- FastAPI exposes the retrieval and RAG endpoints.
- A React playground gives you a browser view over ranking, prompts, answers, and citations.
- Experiment scripts produce repeatable retrieval metrics and saved traces.

> [!NOTE]
> This repository is not trying to be a one-line `ask()` abstraction. It is closer to a workbench: useful when you want to inspect, compare, and tune a RAG pipeline instead of hoping the answer is grounded.

A normal development pass looks something like this:

1. Index a small dataset, usually `scifact` first.
2. Compare BM25, dense, and hybrid results for the same query.
3. Check whether relevant evidence appears in the top-k chunks.
4. Inspect the prompt that is sent to Ollama.
5. Generate an answer and verify that citations match real retrieved chunk IDs.
6. Run retrieval metrics before trusting qualitative RAG examples.
7. Save the configuration next to any metrics you care about.

### Why the project exists

RAG failures are often hard to spot. A fluent answer can be unsupported. A citation can look real while pointing to a chunk that was never retrieved. A dense retriever can return text that sounds related but does not contain the needed evidence. A BM25 result can score highly because of term overlap while missing the actual claim.

This project makes those cases easier to catch. It does not replace careful evaluation, but it gives you the pieces needed to do it properly.

---

## :package: What is included

The repository combines a runnable application with experiment tooling. That is intentional. The same retrieval code can be used from the CLI, the API, or the web playground.

**Indexing path.** Documents are loaded from BEIR-style datasets, split into chunks, embedded with MiniLM, and written to Weaviate with chunk IDs, document IDs, titles or metadata, text, and vectors.

**Retrieval path.** Queries can be executed with BM25, dense search, or hybrid fusion. The same `top_k` and `alpha` controls are available from scripts and from the UI.

**Generation path.** Retrieved chunks are formatted into a prompt, sent to an Ollama model, and returned with citation diagnostics.

**Evaluation path.** Retrieval runs can be scored with Recall@10, MRR, and nDCG@10. RAG demos can save prompts, retrieved chunks, answers, and citation checks.

A good first local configuration is:

```text
dataset       = scifact
model         = gemma2:2b
chunk_size    = 512
overlap       = 64
top_k         = 10
hybrid alpha  = 0.5
embedding     = sentence-transformers/all-MiniLM-L6-v2
```

> [!IMPORTANT]
> Treat these as starting values, not universal defaults. The real source of truth should be the YAML files in `configs/`.

---

[Index](./00-index.md) · [Index](./00-index.md) · [Next](./02-architecture.md)
