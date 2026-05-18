# Evaluation runners, metrics, and order of experiments

[Previous](./05-rag-and-citations.md) · [Index](./00-index.md) · [Next](./07-web-playground.md)

---

## :test_tube: Experiments

The experiment scripts keep evaluation from becoming “I tried a few questions and it looked good.” Use the UI for inspection, but use scripts for comparisons.

### Runners

- `run_indexing` builds or rebuilds dataset indexes.
- `run_retrieval_eval` scores retrieval with qrels.
- `run_testing` runs calibration sweeps.
- `run_rag_demo` saves example RAG traces.
- `run_single` prints one detailed trace for debugging.

<details>
<summary><b>Show experiment commands</b></summary>

```bash
python3 -m src.experiments.run_indexing
python3 -m src.experiments.run_retrieval_eval
python3 -m src.experiments.run_testing
python3 -m src.experiments.run_rag_demo
python3 -m src.experiments.run_single
```

</details>

<details>
<summary><b>Show common variants</b></summary>

```bash
# Index one dataset
python3 -m src.experiments.run_indexing --dataset scifact

# Re-index with a custom chunk size
python3 -m src.experiments.run_indexing --dataset scifact --chunk-size 512 --recreate

# Evaluate hybrid retrieval
python3 -m src.experiments.run_retrieval_eval --dataset scifact --top-k 10 --alpha 0.5

# Skip chunk-size sweeps when tuning only alpha/top-k
python3 -m src.experiments.run_testing --skip-chunk

# Print one detailed trace
python3 -m src.experiments.run_single --dataset scifact --top-k 5 --alpha 0.5
```

</details>

### Metrics that matter first

**Recall@10** tells you whether relevant documents are appearing in the top ten. If this is low, generation will usually fail for the right reason: missing evidence.

**MRR** tells you how early the first relevant result appears. This matters when prompts only include a few chunks.

**nDCG@10** is the best quick view of ranking quality because it rewards useful evidence near the top.

> [!IMPORTANT]
> If retrieval is chunk-level but qrels are document-level, map chunk IDs back to document IDs before scoring. Otherwise one document split into many chunks can make metrics look better than they are.

### Recommended evaluation order

Start small:

1. Index `scifact`.
2. Run BM25, dense, and hybrid at `top_k=10`.
3. Inspect a few failed queries with `run_single`.
4. Sweep `alpha`: `0.0`, `0.25`, `0.5`, `0.75`, `1.0`.
5. Try chunk sizes such as `256`, `512`, and `768` only after retrieval failures suggest chunking is the issue.
6. Run RAG demos after retrieval looks acceptable.

---

[Previous](./05-rag-and-citations.md) · [Index](./00-index.md) · [Next](./07-web-playground.md)
