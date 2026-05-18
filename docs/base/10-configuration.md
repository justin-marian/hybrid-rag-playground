# YAML configuration files

[Previous](./09-results-and-artifacts.md) · [Index](./00-index.md) · [Next](./11-troubleshooting.md)

---

## :gear: Configuration

Configuration belongs in YAML, not scattered through scripts.

### `configs/datasets.yaml`

Use this file for dataset names, splits, and any mapping between local names and BEIR identifiers. Start with one dataset and make sure it appears in `/api/datasets` after indexing.

### `configs/retrieval.yaml`

This is the main file for retrieval behavior. It should make these values explicit:

```yaml
chunking:
  chunk_size: 512
  overlap: 64

embedding:
  model_name: sentence-transformers/all-MiniLM-L6-v2
  batch_size: 32

retrieval:
  default_mode: hybrid
  top_k: 10
  alpha: 0.5
```

### `configs/rag.yaml`

This file should define the Ollama model, prompt template, temperature, and context limits. For citation-aware generation, the prompt must preserve:

```text
{query}
{context_block}
```

### `configs/sweep.yaml`

Keep sweeps small until the baseline works:

```yaml
top_k: [5, 10, 20]
alpha: [0.0, 0.25, 0.5, 0.75, 1.0]
chunk_size: [256, 512, 768]
```

> [!WARNING]
> Alpha and top-k sweeps reuse the same index. Chunk-size sweeps usually require re-indexing.

---

[Previous](./09-results-and-artifacts.md) · [Index](./00-index.md) · [Next](./11-troubleshooting.md)
