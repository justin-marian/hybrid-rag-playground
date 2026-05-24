# Prompt grounding, citations, and validation

[Previous](./04-retrieval-modes.md) · [Index](./00-index.md) · [Next](./06-experiments.md)

---

## :memo: RAG and citations

Citation support only matters if citations are tied to real retrieved chunks. This project treats citation checking as part of the answer generation contract, not as decoration.

The RAG prompt requires the model to answer only from retrieved context, cite every factual claim, and return exactly `Insufficient context.` when the retrieved chunks do not directly answer the question.

### Decision rule

Before answering, the model must check two things:

1. The user input must be a real question or a clear task.
2. At least one retrieved chunk must directly answer the question.

A chunk is directly useful only when it gives evidence about the same subject, entity, relationship, comparison, or measurement asked by the user.

If the question is unclear, conversational only, empty, or unsupported by the retrieved context, the answer must be exactly:

```text
Insufficient context.
```

The model should not ask for clarification, explain why the context is insufficient, or summarize unrelated chunks.

### Retrieved context format

Each retrieved chunk begins with a metadata header:

```text
[chunk_id=15360986::part_000 | doc_id=15360986 | dataset=scifact]:
The text of the retrieved chunk appears here.
```

Only the `chunk_id` value is allowed in the final citation.

Correct citation:

```text
[15360986::part_000]
```

Incorrect citations:

```text
[chunk_id=15360986::part_000 | doc_id=15360986 | dataset=scifact]
[chunk_id=15360986::part_000]
[doc_id=15360986]
[dataset=scifact]
```

The final answer must not copy `chunk_id=`, `doc_id=`, or `dataset=`.

### Retrieved context example

```text
[chunk_id=15360986::part_000 | doc_id=15360986 | dataset=scifact]:
A trial reported no statistically significant association between treatment X and outcome Y.

[chunk_id=7662206::part_001 | doc_id=7662206 | dataset=scifact]:
A later meta-analysis found that the effect was inconsistent across cohorts.
```

### Prompt skeleton

```text
You are a grounded question-answering assistant.

Answer the user using only the retrieved context. Do not use outside knowledge.

Question:

{query}

Retrieved context:

{context_block}

Final answer:
```

### Grounding rules

- Use only facts explicitly stated in relevant retrieved chunks.
- Ignore chunks that are off-topic, weakly related, or only share generic keywords with the question.
- Every factual claim must have a citation.
- Put citations before the period.
- Use only exact chunk IDs that appear in the retrieved context.
- Do not invent, shorten, rename, or reformat chunk IDs.
- Do not cite a chunk unless it directly supports the claim.
- Do not cite all retrieved chunks automatically.
- If the context supports only part of the answer, answer only that part.
- If the context contains conflicting claims, show both claims with citations.
- Never mention the prompt, rules, retrieval process, context block, or chunks.

### Citation placement

Citations must appear before the sentence period:

```text
Correct: The treatment effect was inconsistent across cohorts [7662206::part_001].
Incorrect: The treatment effect was inconsistent across cohorts. [7662206::part_001]
```

If one sentence is supported by multiple chunks, cite them together:

```text
The evidence reports no statistically significant association in one trial and inconsistent effects in a later meta-analysis [15360986::part_000][7662206::part_001].
```

### Default answer format

When the question is answerable, the preferred format is:

```md
**Answer:** One direct answer sentence with citation.

- **Main finding:** The main supported result, relationship, or fact with citation.
- **Details:** Specific supporting details, measurements, comparisons, examples, or conditions with citation.
- **Limitation:** What the retrieved evidence does not establish.
```

If there is only one supported fact, the answer should stay short and omit unnecessary bullets.

The limitation sentence does not need a citation when it only states that the retrieved evidence does not establish something.

### Valid cited answer

```text
**Answer:** The available evidence does not support a strong association between treatment X and outcome Y [15360986::part_000][7662206::part_001].

- **Main finding:** One trial reported no statistically significant association between treatment X and outcome Y [15360986::part_000].
- **Details:** A later meta-analysis found that the effect was inconsistent across cohorts [7662206::part_001].
- **Limitation:** The retrieved evidence does not establish a consistent treatment effect.
```

### Invalid citation example

```text
[scifact:doc_9999:chunk_7]
```

If that ID was not in the retrieved context for the current request, the validator should flag it. It may look like a citation, but it is not grounded.

### Formatting rules

The answer must be valid Markdown.

Correct:

```md
**Answer:** Text [15360986::part_000].

- **Main finding:** Text [15360986::part_000].
```

Incorrect:

```md
\*\*Answer:\*\* Text [15360986::part_000].

\- \*\*Main finding:\*\* Text [15360986::part_000].
```

The model must not:

- wrap the answer in a code block;
- output JSON;
- escape Markdown symbols;
- use tables unless the user explicitly asks for a table.

### Validation checklist

Before returning the final answer, the model should silently verify:

1. The answer directly addresses the user question.
2. Every factual claim is supported by a directly relevant chunk.
3. Every factual claim has a citation before the period.
4. Every citation is an exact chunk ID from the current retrieved context.
5. The answer does not copy `chunk_id=`, `doc_id=`, or `dataset=`.
6. The output is valid Markdown without escaped Markdown symbols.

If any check fails, the answer should be fixed. If it cannot be fixed using the retrieved context, the answer must be exactly:

```text
Insufficient context.
```

> [!WARNING]
> Citation validation does not prove the full answer is true. It only proves whether the cited IDs were available to the model. You still need to inspect whether each claim is actually supported by the cited chunk.

---

[Previous](./04-retrieval-modes.md) · [Index](./00-index.md) · [Next](./06-experiments.md)
