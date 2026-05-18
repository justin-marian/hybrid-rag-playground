# Frontend workflow and UI debugging

[Previous](./06-experiments.md) · [Index](./00-index.md) · [Next](./08-api.md)

---

## :computer: Web playground

The playground is for debugging, not only for demos.

Use it in this order:

1. Check health status.
2. Select an indexed dataset.
3. Run retrieve mode with BM25, dense, and hybrid.
4. Compare chunk text, scores, document IDs, and duplicates.
5. Open the prompt viewer.
6. Run RAG mode.
7. Check citation chips and validation warnings.

<details>
<summary><b>Show web startup commands</b></summary>

```bash
./run_api.sh
cd web
bun install
bun run dev
```

</details>

A useful UI trace should make the same query reproducible from the CLI or API. If the UI only shows the final answer, it is hiding the most important part of RAG debugging.

---

[Previous](./06-experiments.md) · [Index](./00-index.md) · [Next](./08-api.md)
