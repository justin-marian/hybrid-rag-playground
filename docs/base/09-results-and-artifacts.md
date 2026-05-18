# Expected outputs and run context

[Previous](./08-api.md) · [Index](./00-index.md) · [Next](./10-configuration.md)

---

## :bar_chart: Results and artifacts

Expected outputs should be predictable enough to compare across runs:

- `data/results/{dataset}/retrieval_metrics.csv`
- `images/{dataset}/retrieval_comparison_table.md`
- `images/{dataset}/retrieval_comparison_table.csv`
- `data/results/{dataset}/rag/rag_demo.json`
- `images/{dataset}/rag_demo.md`
- `data/results/{dataset}/sweep_results.csv`
- `images/{dataset}/sweep_ndcg10.png`

When saving an important result, keep the run context with it:

```text
dataset=scifact
retriever=hybrid
top_k=10
alpha=0.5
chunk_size=512
overlap=64
embedding_model=sentence-transformers/all-MiniLM-L6-v2
ollama_model=gemma2:2b
collection=<configured collection name>
```

> [!CAUTION]
> Do not compare metrics from different index states as if they were the same experiment. Changing chunk size, overlap, embedding model, or collection schema changes the retrieval problem.

---

[Previous](./08-api.md) · [Index](./00-index.md) · [Next](./10-configuration.md)
