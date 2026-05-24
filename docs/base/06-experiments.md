# Evaluation runners, metrics, and order of experiments

[Previous](./05-rag-and-citations.md) · [Index](./00-index.md) · [Next](./07-web-playground.md)

---

## :test_tube: Experiments

The experiment scripts keep evaluation from becoming “I tried a few questions and it looked good.” Use the UI for inspection, but use scripts for comparisons.

### Runners

- `run_indexing_eval` builds or rebuilds dataset indexes.
- `run_retrieval_eval` scores retrieval with qrels.
- `run_testing` runs calibration sweeps.
- `run_rag_demo` saves example RAG traces.
- `run_single` prints one detailed trace for debugging.

<details>
<summary><b>Show experiment commands</b></summary>

```bash
python3 -m src.experiments.run_indexing_eval
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
python3 -m src.experiments.run_indexing_eval --dataset scifact

# Re-index with a custom chunk size
python3 -m src.experiments.run_indexing_eval --dataset scifact --chunk-size 512 --recreate

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

### Full sequence to reproduce all results

Run the full evaluation sequence from the project root. This order ensures that the Weaviate collections are created first, retrieval metrics are computed after indexing, calibration results are generated after baseline evaluation, and the final report can collect all produced artifacts.

<details>
<summary><b>Show full result-generation sequence</b></summary>

```bash
# 0. Start FastAPI -- separate terminal
bash ./run_api.sh

# 1. Start Weaviate  -- separate terminal
docker compose -f docker/docker-compose.yml up -d weaviate

curl http://localhost:18080/v1/.well-known/ready

# 2. Index BEIR datasets into Weaviate -- separate terminal
uv run python -m src.experiments.run_indexing_eval \
  --config retrieval.yaml \
  --datasets-config datasets.yaml \
  --dataset nfcorpus \
  --dataset scifact \
  --dataset fiqa \
  --recreate


# 3. Run retrieval evaluation
uv run python -m src.experiments.run_retrieval_eval \
  --config retrieval.yaml \
  --datasets-config datasets.yaml \
  --dataset nfcorpus \
  --dataset scifact \
  --dataset fiqa


# 4. Run calibration / hyperparameter testing
uv run python -m src.experiments.run_testing \
  --retrieval-config retrieval.yaml \
  --test-calibration-config system_arch.yaml \
  --datasets-config datasets.yaml \
  --dataset nfcorpus

uv run python -m src.experiments.run_testing \
  --retrieval-config retrieval.yaml \
  --test-calibration-config system_arch.yaml \
  --datasets-config datasets.yaml \
  --dataset scifact

uv run python -m src.experiments.run_testing \
  --retrieval-config retrieval.yaml \
  --test-calibration-config system_arch.yaml \
  --datasets-config datasets.yaml \
  --dataset fiqa


# 5. Optional: run one detailed query trace
uv run python -m src.experiments.run_single \
  --retrieval-config retrieval.yaml \
  --rag-config rag.yaml \
  --datasets-config datasets.yaml \
  --dataset scifact \
  --top-k 5 \
  --alpha 0.5 \
  --query "Are statins effective for reducing cholesterol?"


# 6. Optional: run RAG demo traces
uv run python -m src.experiments.run_rag_demo \
  --retrieval-config retrieval.yaml \
  --rag-config rag.yaml \
  --datasets-config datasets.yaml \
  --dataset scifact \
  --retriever hybrid \
  --top-k 5 \
  --alpha 0.5 \
  --num-queries 5


# 7. Generate final evaluation report with hyperparameters
uv run python -m src.evaluation.report
```

</details>

### Expected generated artifacts

After the full sequence, the main artifacts should be:

- `data/results/retrieval_metrics.csv`: long-form retrieval results for BM25, dense, and hybrid retrieval.
- `data/retrieval_comparison_table.csv`: wide comparison table across datasets and metrics.
- `docs/RETRIEVAL_COMPARE_TABLE.md`: Markdown retrieval comparison table.
- `data/results/sweep_results.csv`: hyperparameter calibration results, if generated by `run_testing`.
- `images/`: calibration plots and experiment figures.
- `data/results/rag/rag_demo.json`: saved RAG demo traces, if `run_rag_demo` was executed.
- `docs/RAG_DEMO.md`: manual RAG inspection table, if `run_rag_demo` was executed.
- `docs/EVALUATION_REPORT.md`: final report containing retrieval results, calibration highlights, RAG traces, and hyperparameter names used for the results.

---

[Previous](./05-rag-and-citations.md) · [Index](./00-index.md) · [Next](./07-web-playground.md)
