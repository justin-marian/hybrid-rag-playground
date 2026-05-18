# Architecture, layers, and main components

[Previous](./01-overview.md) · [Index](./00-index.md) · [Next](./03-quickstart.md)

---

## :building_construction: Architecture

<div align="center">
  <img src="../../images/architecture.png" alt="Hybrid RAG architecture" width="950">
  <br>
  <sub><b>Figure 1.</b> Local-first retrieval, evaluation, automation, and citation-aware generation.</sub>
</div>

The architecture is split so that each failure can be traced to a specific layer. If a final answer is bad, the problem is not automatically “the LLM.” It may be the dataset selection, chunking, embedding model, retriever mode, `top_k`, prompt format, citation parser, or the generation settings.

### Main components

| Component | What it does |
|---|---|
| BEIR loader | Reads corpus, queries, and qrels for benchmark-style retrieval experiments. |
| Chunking pipeline | Converts documents into smaller evidence units that can be ranked and cited. |
| MiniLM embedding step | Creates dense vectors used by semantic and hybrid retrieval. |
| Weaviate | Stores chunk text, metadata, vectors, and supports BM25/dense/hybrid search. |
| Retriever wrapper | Gives BM25, dense, and hybrid retrieval a common interface. |
| Prompt builder | Turns retrieved chunks into a context block with citation instructions. |
| Ollama client | Sends the grounded prompt to a local model. |
| Citation validator | Checks whether generated citations match retrieved chunk IDs. |
| Experiment runners | Rebuild indexes, score retrieval, run sweeps, and save traces. |
| Web playground | Makes retrieval, prompts, answers, and citation checks visible. |

The key design choice is to keep retrieval and generation separate. You should be able to run retrieval alone, inspect the chunks, and decide whether the generator has enough evidence before asking the model to answer.

> [!TIP]
> Debug from left to right. Dataset and index first, retriever second, prompt third, model last.

---

[Previous](./01-overview.md) · [Index](./00-index.md) · [Next](./03-quickstart.md)
