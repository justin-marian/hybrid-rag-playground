# Local setup and first end-to-end run

[Previous](./02-architecture.md) · [Index](./00-index.md) · [Next](./04-retrieval-modes.md)

---

## :rocket: Quickstart

This setup starts the local services and runs a small end-to-end test. Commands are hidden so the README stays readable.

### 1. Check requirements

You need Python, Docker, Ollama, Bun, and Git. Use Python `3.10+` and Docker Compose V2.

<details>
<summary><b>Show validation commands</b></summary>

```bash
python3 --version
docker --version
docker compose version
ollama --version
bun --version
git --version
```

</details>

> [!WARNING]
> Start with one small dataset. Indexing every dataset before the stack is validated makes debugging slower and usually does not teach you anything useful.

### 2. Clone the repository

<details>
<summary><b>Show clone commands</b></summary>

```bash
git clone https://github.com/justin-marian/hybrid-rag-playground
cd hybrid-rag-playground
```

</details>

All commands below assume you are in the repository root.

### 3. Create the Python environment

Use a virtual environment for the backend, evaluation scripts, Weaviate client, embedding packages, and plotting tools.

<details>
<summary><b>Show Python environment commands</b></summary>

```bash
python3 -m venv .venv
```

Linux or macOS:

```bash
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Upgrade packaging tools:

```bash
python3 -m pip install --upgrade pip setuptools wheel
```

</details>

If later commands cannot import project modules, check that the environment is activated and that the package was installed in editable mode.

### 4. Install backend dependencies

<details>
<summary><b>Show installation commands</b></summary>

```bash
pip install -e ".[dev]"
```

If the project does not define a `dev` extra:

```bash
pip install -e .
```

</details>

After this step, experiment modules should run from the repository root with `python3 -m src.experiments...`.

### 5. Start Weaviate

Weaviate must be running before indexing and retrieval.

<details>
<summary><b>Show Weaviate commands</b></summary>

```bash
docker compose -f docker/docker-compose.yml up -d
```

Check the container:

```bash
docker compose -f docker/docker-compose.yml ps
```

Check readiness:

```bash
curl -s http://localhost:18080/v1/.well-known/ready
```

Expected output:

```text
true
```

</details>

> [!CAUTION]
> Use `--recreate` only when you intentionally want to rebuild the index. It can delete the existing collection for that dataset or configuration.

### 6. Start Ollama and pull a model

The examples use `gemma2:2b` because it is small enough for local testing. For stronger answer quality, use the model configured in `configs/rag.yaml`.

<details>
<summary><b>Show Ollama commands</b></summary>

Start Ollama if needed:

```bash
ollama serve
```

In another terminal:

```bash
ollama pull gemma2:2b
ollama list
```

</details>

> [!IMPORTANT]
> The model name must match exactly. `gemma2:2b` and `gemma2` are different model names for Ollama.

### 7. Check configuration before indexing

Before writing chunks to Weaviate, open the config files and check the active dataset, chunking settings, embedding model, collection name, retriever defaults, and Ollama model.

<details>
<summary><b>Show configuration inspection commands</b></summary>

```bash
ls configs
```

```bash
cat configs/datasets.yaml
cat configs/retrieval.yaml
cat configs/rag.yaml
cat configs/sweep.yaml
```

</details>

The first run should be boring. Use `scifact`, `top_k=10`, `alpha=0.5`, and a moderate chunk size such as `512`. Once that works, change one variable at a time.

### 8. Index one dataset

Indexing creates chunk objects in Weaviate. A useful chunk object should contain at least a chunk ID, source document ID, text, and metadata. Dense retrieval also requires the embedding vector.

<details>
<summary><b>Show indexing commands</b></summary>

Run default indexing:

```bash
python3 -m src.experiments.run_indexing_eval
```

Index only SciFact:

```bash
python3 -m src.experiments.run_indexing_eval --dataset scifact
```

Re-index SciFact with a specific chunk size:

```bash
python3 -m src.experiments.run_indexing_eval --dataset scifact --chunk-size 512 --recreate
```

</details>

What should happen on rerun depends on the implementation, but it should be explicit: skip existing data, append safely, or fail clearly. Silent duplicate insertion is a bug worth fixing.

### 9. Run retrieval evaluation

Do this before spending time on generation. If relevant documents do not appear in the retrieved set, the model cannot cite them.

<details>
<summary><b>Show retrieval evaluation commands</b></summary>

Run default evaluation:

```bash
python3 -m src.experiments.run_retrieval_eval
```

Evaluate a balanced hybrid setup:

```bash
python3 -m src.experiments.run_retrieval_eval --dataset scifact --top-k 10 --alpha 0.5
```

</details>

A useful first result is a side-by-side comparison of BM25, dense, and hybrid retrieval on the same dataset and `top_k`.

### 10. Run one RAG trace

A single detailed trace is better than a large demo when debugging. It should expose the query, retrieved chunks, scores, prompt, answer, citations, and invalid citations.

<details>
<summary><b>Show RAG trace commands</b></summary>

```bash
python3 -m src.experiments.run_single --dataset scifact --top-k 5 --alpha 0.5
```

Run the demo set:

```bash
python3 -m src.experiments.run_rag_demo
```

</details>

A good trace should answer five questions: was the right evidence retrieved, were chunk IDs visible in the prompt, did the model copy valid IDs, did the answer add unsupported claims, and did validation catch bad citations?

### 11. Start the API

<details>
<summary><b>Show FastAPI commands</b></summary>

```bash
./run_api.sh
```

Open:

```text
http://localhost:8080/docs
```

Health check:

```bash
curl -s http://localhost:8080/api/health
```

</details>

Keep this terminal open while using the frontend. The logs are usually the quickest way to spot schema mismatches, missing collections, or Ollama connection failures.

### 12. Start the web playground

<details>
<summary><b>Show web commands</b></summary>

```bash
cd web
bun install
bun run dev
```

Open:

```text
http://localhost:5173
```

</details>

Start with the health panel, then dataset selection, then retrieve mode. Run RAG only after the retrieved chunks look reasonable.

---

[Previous](./02-architecture.md) · [Index](./00-index.md) · [Next](./04-retrieval-modes.md)
