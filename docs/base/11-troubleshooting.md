# Common runtime and evaluation issues

[Previous](./10-configuration.md) · [Index](./00-index.md) · [Next](./12-roadmap.md)

---

## :wrench: Troubleshooting

### Weaviate is not ready

<details>
<summary><b>Show Weaviate troubleshooting commands</b></summary>

```bash
docker compose -f docker/docker-compose.yml ps
curl -s http://localhost:18080/v1/.well-known/ready
docker compose -f docker/docker-compose.yml restart
```

</details>

Common causes: Docker is stopped, port `18080` is busy, or the collection schema no longer matches the current code/config.

### Ollama is unreachable

<details>
<summary><b>Show Ollama troubleshooting commands</b></summary>

```bash
ollama serve
ollama list
ollama pull gemma2:2b
```

</details>

Check that `configs/rag.yaml` uses exactly the same model name shown by `ollama list`.

### Retrieval returns no chunks

Usually this means the dataset was not indexed, the API points to the wrong collection, the dataset name does not match, or Weaviate was recreated after indexing.

<details>
<summary><b>Show retrieval debugging commands</b></summary>

```bash
python3 -m src.experiments.run_indexing_eval --dataset scifact
python3 -m src.experiments.run_single --dataset scifact --top-k 5 --alpha 0.5
curl -s http://localhost:8080/api/datasets
```

</details>

### Citation chips are missing

Check the prompt first. The model cannot cite chunk IDs that were never included in the context block.

A valid citation should look like:

```text
[scifact:doc_1397:chunk_0]
```

If the model uses a different format, either update the prompt or update the parser.

### Evaluation looks too good

Check whether duplicate chunks from the same source document are being counted as separate hits. For BEIR-style qrels, score at document level, not chunk level.

### Embedding is slow

Lower the embedding batch size first. Then reduce enabled datasets. Avoid changing chunk size and batch size at the same time, because that makes the cause of the improvement unclear.

---

[Previous](./10-configuration.md) · [Index](./00-index.md) · [Next](./12-roadmap.md)
