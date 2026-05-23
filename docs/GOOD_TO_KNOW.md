# Good to know

Operational notes and gotchas while running the project. **Keep your existing
content: this file is only a placeholder if it didn't already exist.**

## Embedding cache

- Cached under `data/cache/embeddings/<model>_norm1.npz` as a single compressed numpy archive (`keys`, `vecs`).
- Cache is keyed by `sha1(text)`. Identical chunk text across datasets shares vectors automatically.
- Safe to delete the cache: it will be rebuilt on the next run.

## Weaviate

- Anonymous access is enabled in the docker-compose. Do **not** expose the container outside `localhost` without adding auth first.
- gRPC must be reachable (port 15051): the v4 Python client uses gRPC for the batch insertion path; falling back to REST-only is much slower.
- `client.collections.exists(name)` is the cheap way to check before creating.

## Chunk IDs and UUIDs

- Object UUIDs in Weaviate are deterministic (`uuid5(NAMESPACE_URL, chunk_id)`), so re-running `run_indexing_eval` overwrites instead of duplicating.
- `chunk_id` follows the `<doc_id>::chunk_<index>` convention so we can collapse back to `doc_id` for IR metrics.

## Metric correctness

- IR metrics (Recall@10, MRR, nDCG@10) operate on **doc-level** rankings. Chunks are deduplicated to their `doc_id` *before* scoring, so two chunks from the same paper count once.
- nDCG uses graded relevance from qrels (BEIR provides integer scores).
