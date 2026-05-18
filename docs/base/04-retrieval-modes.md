# BM25, dense MiniLM, and hybrid retrieval

[Previous](./03-quickstart.md) · [Index](./00-index.md) · [Next](./05-rag-and-citations.md)

---

## :mag: Retrieval modes

The three retrieval modes are useful for different failure cases.

### BM25

BM25 is the lexical baseline. It works well when the query shares terms with the evidence: entities, acronyms, paper-specific wording, scientific claims, error codes, identifiers, and exact phrases. It is also the easiest mode to reason about. If a term is not in the chunk, BM25 cannot match it.

### Dense MiniLM retrieval

Dense retrieval compares embeddings rather than exact tokens. It can find paraphrases and related wording, which helps when the query and document do not use the same phrasing.

The weakness is precision. Dense retrieval can return chunks that are “about the same topic” without containing the exact evidence needed for the answer.

### Hybrid retrieval

Hybrid retrieval combines sparse and dense signals. The `alpha` value controls the balance:

```text
alpha = 0.0  -> mostly BM25
alpha = 0.5  -> balanced sparse + dense
alpha = 1.0  -> mostly dense
```

A sensible tuning order is:

1. Compare BM25, dense, and hybrid at the same `top_k`.
2. Sweep `alpha` while keeping the index fixed.
3. Increase `top_k` if relevant chunks exist but are ranked too low.
4. Change chunk size only when chunks are clearly too small or too broad.

> [!NOTE]
> There is no universal best `alpha`. Scientific claim datasets often benefit from stronger lexical evidence, while paraphrased questions may need more dense retrieval.

---

[Previous](./03-quickstart.md) · [Index](./00-index.md) · [Next](./05-rag-and-citations.md)
