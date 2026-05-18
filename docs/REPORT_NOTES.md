# Technical Report Notes

This file is a working scratchpad to assemble the final 3–4 page PDF report.
It maps each report section to the artifacts produced by the code, so writing
up the PDF mostly becomes copy/edit work.

---

## 1. Pipeline overview (≈ ½ page)

Suggested talking points:

- BEIR datasets used: NFCorpus (~3.6K, medical), SciFact (~5K, scientific
  fact-checking), FiQA (~57K, financial Q&A).
- Chunking: fixed-size 256 tokens, 10% overlap (token-aware using the MiniLM
  tokenizer, falling back to word-level).
- Embedder: `sentence-transformers/all-MiniLM-L6-v2`, 384-d, cosine
  (normalized embeddings).
- Vector DB: Weaviate 1.27 in BYO-vectors mode, HNSW (default parameters), BM25
  on the `text` property (default `k1=1.2`, `b=0.75`). One collection per
  dataset (`Nfcorpus`, `Scifact`, `Fiqa`).
- Retrievers: BM25 (`collection.query.bm25`), dense (`near_vector`), hybrid
  (`hybrid(alpha=0.5)`).
- LLM: Ollama running `gemma2:2b` (default) or `llama3.2:3b`.
- Metric scope: all metrics computed on **doc-level** rankings (chunks are
  collapsed to their source `doc_id`, deduplicating at first occurrence).

Diagram idea (optional): query → embed → BM25 || ANN → hybrid fusion → top-k
chunks → prompt → Ollama → cited answer.

---

## 2. Retrieval comparison table (Cerința 2)

Insert the contents of `docs/retrieval_comparison_table.md` here, or import
`docs/retrieval_comparison_table.csv` directly into the PDF as a table.

Source data: `data/results/retrieval_metrics.csv`.

### Discussion checklist

Look at the three datasets side-by-side and confirm/refute the following claims
in the report:

- **BM25 wins on fact-checking** (SciFact tends to favor BM25 because queries
  and relevant passages share rare technical vocabulary verbatim). If your
  numbers show this, say so explicitly.
- **Dense wins on FiQA** (financial Q&A is paraphrase-heavy; semantic matching
  beats lexical overlap). Verify.
- **NFCorpus is in between** (medical/nutrition has both technical jargon and
  paraphrasing). The hybrid is usually the safe choice.
- **No retriever dominates across all 3 datasets and all 3 metrics.** This is
  the central observation the report must make.

If your numbers contradict the typical pattern, that's fine — describe what
you actually see and propose a plausible cause.

---

## 3. Dataset chosen for RAG

Default choice: **SciFact**. Justification:

- Mid-sized corpus (~5K), fast to iterate on.
- Claims-style queries make hallucinations easy to spot (the LLM either cites
  a chunk that supports the claim or it doesn't).
- Both BM25 and dense have non-trivial gaps, so the hybrid retriever's value
  is most visible here.

If your retrieval table points at a different dataset (e.g., FiQA looks
much more interesting), swap this section accordingly. Edit
`configs/rag.yaml` → `rag.dataset` and re-run the demo.

---

## 4. RAG manual evaluation

- Run `python -m src.experiments.run_rag_demo`.
- Open `docs/rag_demo.md`. Read the answer + the top-3 chunk IDs for each of
  the 10 queries.
- Fill the `Notes` column with one of: `correct`, `partial`, `hallucination`.
- The spec requires **at least one** `hallucination` case. Likely sources of
  hallucination to watch for:
  - The LLM cites a chunk that doesn't actually contain the claim it's
    attributed to.
  - The LLM invents a citation ID that isn't in the context.
  - The LLM merges two adjacent chunks and attributes a number from one to a
    claim in the other.
  - The LLM uses prior-training knowledge (e.g. a famous trial) and slaps a
    `[chunk_id=...]` on it.
- In the report, paste the failing query + the answer + a brief diagnosis
  (which chunk is cited, what the chunk actually says, where the model went
  wrong).

---

## 5. Calibration sweep

- Run `python -m src.experiments.run_sweep`.
- Insert `docs/{dataset}_/sweep_ndcg10.png` into the report.
- The script prints the recommended configuration to stdout. Quote those
  numbers in the report and justify them in 2–3 sentences:
  - Optimal alpha is usually somewhere in 0.25–0.75 for these datasets; α=0 or
    α=1 typically lose to the mix.
  - Larger `top_k` raises Recall@10 mechanically but can hurt the RAG answer
    (more distractor chunks → more hallucinations). Discuss the trade-off.
  - Chunk size: smaller chunks (256) tend to improve nDCG (more focused
    matches) but reduce context per chunk for the LLM. 512 is often the sweet
    spot for RAG answer quality even when retrieval nDCG is slightly lower.

---

## 6. Reproducibility statement (mandatory)

Copy this block, verbatim, into the PDF:

> Reproduction (Linux/macOS, ~10 GB disk, ~30 min on CPU):
>
> 1. `docker compose -f docker/docker-compose.yml up -d`
> 2. `ollama pull gemma2:2b`
> 3. `pip install -e .`
> 4. `python -m src.experiments.run_indexing`
> 5. `python -m src.experiments.run_retrieval_eval`
> 6. `python -m src.experiments.run_rag_demo`
> 7. `python -m src.experiments.run_sweep`
>
> All paths are project-root-relative. The BEIR datasets are downloaded
> automatically into `data/beir/` and are **not** part of the submission archive.

---

## 7. Video demo notes (≤ 2 minutes)

Recommended script for the screen recording:

1. `docker compose ... up -d` (5 s, just show the container is up).
2. `python -m src.experiments.run_demo_single --query "..."` (the heavy lift).
3. Visually walk through the four panels printed by `run_demo_single`:
   - BM25 top-5
   - Dense top-5
   - Hybrid top-5
   - Final RAG answer with `[chunk_id=...]` citations
4. Point out one chunk that all three retrievers agree on, and one where they
   disagree. End on the cited final answer.

Encode the video as H.264 (1080p, ~2 Mbps) to stay well under the 50 MB Moodle
limit.

---

## 8. Files to attach to the submission archive

Include:
- `src/`, `configs/`, `docker/`, `images/`, `docs/`, `pdfs/`
- `pyproject.toml`, `setup.py`, `README.md`, `.gitignore`
- Plots: `docs/{dataset}_/retrieval_comparison_table.*`, `images/{dataset}_/sweep_ndcg10.png`
- `docs/rag_demo.md` (with the manual annotations filled in)

Exclude (must NOT be in the archive):
- `data/beir/` (datasets)
- `data/cache/` (embedding cache)
- `data/results/` (regenerated by the grader)
- `.venv/`, `__pycache__/`, `*.log`
