# FastAPI endpoints and request/response examples

[Previous](./07-web-playground.md) · [Index](./00-index.md) · [Next](./09-results-and-artifacts.md)

---

## :zap: API

The API sits between the frontend, experiment scripts, Weaviate, and Ollama.

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/health` | Check backend dependency status. |
| `GET` | `/api/config` | Return runtime options and frontend defaults. |
| `GET` | `/api/datasets` | List datasets and indexed chunk counts. |
| `POST` | `/api/retrieve` | Run BM25, dense, or hybrid retrieval. |
| `POST` | `/api/rag` | Retrieve evidence, build prompt, generate answer, validate citations. |

<details>
<summary><b>Show API docs URL</b></summary>

```text
http://localhost:8080/docs
```

</details>

### Example retrieval request

<details>
<summary><b>Show JSON request</b></summary>

```json
{
  "dataset": "scifact",
  "query": "Does the evidence support the scientific claim?",
  "mode": "hybrid",
  "top_k": 10,
  "alpha": 0.5
}
```

</details>

### Example RAG response shape

<details>
<summary><b>Show JSON response shape</b></summary>

```json
{
  "answer": "The answer text with [scifact:doc_1397:chunk_0] citations.",
  "chunks": [
    {
      "chunk_id": "scifact:doc_1397:chunk_0",
      "document_id": "doc_1397",
      "title": "Example scientific claim document",
      "score": 0.8124,
      "text": "Retrieved evidence text..."
    }
  ],
  "citations": [
    {
      "chunk_id": "scifact:doc_1397:chunk_0",
      "valid": true
    }
  ],
  "diagnostics": {
    "mode": "hybrid",
    "top_k": 10,
    "alpha": 0.5,
    "invalid_citations": []
  }
}
```

</details>

> [!NOTE]
> The live FastAPI docs are the source of truth if the schema changes.

---

[Previous](./07-web-playground.md) · [Index](./00-index.md) · [Next](./09-results-and-artifacts.md)
