# Prompt grounding, citations, and validation

[Previous](./04-retrieval-modes.md) · [Index](./00-index.md) · [Next](./06-experiments.md)

---

## :memo: RAG and citations

Citation support only matters if citations are tied to real retrieved chunks. This project treats citation checking as part of the response, not as decoration.

### Retrieved context example

```text
[chunk_id: scifact:doc_1397:chunk_0]
title: Example scientific claim document
score: 0.8124
text: The trial reported no statistically significant association between treatment X and outcome Y...

[chunk_id: scifact:doc_2411:chunk_2]
title: Related evidence document
score: 0.7741
text: A later meta-analysis found that the effect was inconsistent across cohorts...
```

### Prompt skeleton

```text
You are a retrieval-grounded assistant.

Use only the evidence in CONTEXT.
Cite factual claims with chunk IDs in square brackets.
If the evidence is insufficient, say that it is insufficient.
Do not invent citations.

QUESTION:
{query}

CONTEXT:
{context_block}

ANSWER:
```

### Valid cited answer

```text
The available evidence does not support a strong association between treatment X and outcome Y. One trial reported no statistically significant association [scifact:doc_1397:chunk_0], and a later meta-analysis found inconsistent effects across cohorts [scifact:doc_2411:chunk_2].
```

### Invalid citation example

```text
[scifact:doc_9999:chunk_7]
```

If that ID was not in the retrieved context for the current request, the validator should flag it. It may look like a citation, but it is not grounded.

> [!WARNING]
> Citation validation does not prove the full answer is true. It only proves whether the cited IDs were available to the model. You still need to inspect whether each claim is actually supported by the cited chunk.

---

[Previous](./04-retrieval-modes.md) · [Index](./00-index.md) · [Next](./06-experiments.md)
