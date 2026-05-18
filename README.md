<div align="center">

<h1>
  Hybrid RAG<br>
  Sparse to Dense Embeddings Playground
</h1>

<p>
  <b>
  Build, inspect, and benchmark a local RAG pipeline where <br>retrieval results, prompts, citations, and generated answers stay fully visible.
  </b>
</p>

<p>
  <a href="docs/base/03-quickstart.md"><img alt="Quickstart" src="https://img.shields.io/badge/Quickstart-local%20setup-2ea44f?style=flat-square&logo=rocket&logoColor=white"></a>
  <a href="docs/base/02-architecture.md"><img alt="Architecture" src="https://img.shields.io/badge/Architecture-RAG%20pipeline-0969da?style=flat-square&logo=dependabot&logoColor=white"></a>
  <a href="docs/base/04-retrieval-modes.md"><img alt="Retrieval" src="https://img.shields.io/badge/Retrieval-BM25%20%7C%20Dense%20%7C%20Hybrid-b91c1c?style=flat-square&logo=semanticweb&logoColor=white"></a>
  <a href="docs/base/06-experiments.md"><img alt="Experiments" src="https://img.shields.io/badge/Experiments-repeatable-8250df?style=flat-square&logo=pytest&logoColor=white"></a>
</p>

<p>
  <img alt="Python" src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white">
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-backend-009688?style=flat-square&logo=fastapi&logoColor=white">
  <img alt="React" src="https://img.shields.io/badge/React-TypeScript-61DAFB?style=flat-square&logo=react&logoColor=black">
  <img alt="TypeScript" src="https://img.shields.io/badge/TypeScript-frontend-3178C6?style=flat-square&logo=typescript&logoColor=white">
  <img alt="Docker" src="https://img.shields.io/badge/Docker-local%20services-2496ED?style=flat-square&logo=docker&logoColor=white">
</p>

<p>
  <img alt="Weaviate" src="https://img.shields.io/badge/Weaviate-vector%20database-00B894?style=flat-square&logo=weaviate&logoColor=white">
  <img alt="Ollama" src="https://img.shields.io/badge/Ollama-local%20LLM-000000?style=flat-square&logo=ollama&logoColor=white">
  <img alt="BEIR" src="https://img.shields.io/badge/BEIR-benchmarks-b91c1c?style=flat-square&logo=googlescholar&logoColor=white">
  <img alt="RAG" src="https://img.shields.io/badge/RAG-grounded%20generation-0a66c2?style=flat-square&logo=openai&logoColor=white">
</p>

<p>
  <img alt="Hybrid Search" src="https://img.shields.io/badge/Hybrid%20Search-sparse%20%2B%20dense-6f42c1?style=flat-square&logo=elasticsearch&logoColor=white">
  <img alt="Citation Validation" src="https://img.shields.io/badge/Citations-validation%20ready-d73a49?style=flat-square&logo=readthedocs&logoColor=white">
  <img alt="Local First" src="https://img.shields.io/badge/Local--first-no%20hosted%20LLM-24292f?style=flat-square&logo=homeassistant&logoColor=white">
  <img alt="Evaluation" src="https://img.shields.io/badge/Evaluation-Recall%40K%20%7C%20MRR%20%7C%20nDCG-1f883d?style=flat-square&logo=chartdotjs&logoColor=white">
</p>

<p>
  <a href="docs/base/01-overview.md"><b>✨ Overview</b></a>
  &nbsp;·&nbsp;
  <a href="docs/base/02-architecture.md"><b>🏗️ Architecture</b></a>
  &nbsp;·&nbsp;
  <a href="docs/base/03-quickstart.md"><b>🚀 Quickstart</b></a>
  &nbsp;·&nbsp;
  <a href="docs/base/04-retrieval-modes.md"><b>🔎 Retrieval</b></a>
  &nbsp;·&nbsp;
  <a href="docs/base/05-rag-and-citations.md"><b>🧾 RAG & Citations</b></a>
</p>

<p>
  <a href="docs/base/06-experiments.md"><b>🧪 Experiments</b></a>
  &nbsp;·&nbsp;
  <a href="docs/base/07-web-playground.md"><b>🖥️ Playground</b></a>
  &nbsp;·&nbsp;
  <a href="docs/base/08-api.md"><b>⚡ API</b></a>
  &nbsp;·&nbsp;
  <a href="docs/base/10-configuration.md"><b>⚙️ Config</b></a>
  &nbsp;·&nbsp;
  <a href="docs/base/11-troubleshooting.md"><b>🛠️ Troubleshooting</b></a>
</p>

</div>

---

## :books: Documentation

The guide is split into focused pages so the root README stays clean and quick to scan.  
Use this map to jump directly into setup, architecture, retrieval, experiments, API usage, or debugging.

| Section | What you will find | Open |
|---|---|---|
| :sparkles: Overview | Project purpose, local-first RAG flow, and what the system exposes for debugging. | [Read overview](docs/base/01-overview.md) |
| :building_construction: Architecture | Pipeline layers, component responsibilities, and how retrieval connects to generation. | [View architecture](docs/base/02-architecture.md) |
| :rocket: Quickstart | Setup order for Docker, Weaviate, Python, Ollama, indexing, API, and frontend. | [Start here](docs/base/03-quickstart.md) |
| :mag: Retrieval modes | BM25, dense MiniLM, hybrid search, `top_k`, and `alpha` tuning. | [Compare retrievers](docs/base/04-retrieval-modes.md) |
| :memo: RAG & citations | Prompt context, chunk IDs, valid citations, invalid citations, and validation logic. | [Check grounding](docs/base/05-rag-and-citations.md) |
| :test_tube: Experiments | Indexing, retrieval evaluation, sweeps, metrics, and repeatable run order. | [Run experiments](docs/base/06-experiments.md) |
| :desktop_computer: Web playground | Browser workflow for inspecting chunks, scores, prompts, answers, and citations. | [Use playground](docs/base/07-web-playground.md) |
| :zap: API | FastAPI routes for health, config, datasets, retrieval, and RAG generation. | [Open API guide](docs/base/08-api.md) |
| :bar_chart: Results | CSV, Markdown, JSON, plots, reports, and expected experiment artifacts. | [Review outputs](docs/base/09-results-and-artifacts.md) |
| :gear: Configuration | Dataset, retrieval, RAG, and sweep YAML settings. | [Edit config](docs/base/10-configuration.md) |
| :wrench: Troubleshooting | Fixes for Weaviate, Ollama, ports, indexing, retrieval, frontend, and citations. | [Debug issues](docs/base/11-troubleshooting.md) |
| :world_map: Roadmap | Planned improvements and future extensions. | [See roadmap](docs/base/12-roadmap.md) |

> [!NOTE]
> For a first local run, start with the **:rocket: Quickstart** page.
>
> For understanding the system design, start with **:building_construction: Architecture** and then continue with **:mag: Retrieval modes**.

---

<div align="center">
  <h2>
    <img src="https://raw.githubusercontent.com/seanprashad/slackmoji/master/emoji/llamas/llama-sunglasses-gif.gif" width="34" alt="llama sunglasses">
    🌠 Architecture ✨
    <img src="https://raw.githubusercontent.com/seanprashad/slackmoji/master/emoji/llamas/llama-awesome-gif.gif" width="34" alt="llama awesome">
  </h2>
</div>

<div align="center">
  <img src="images/architecture.png" alt="Hybrid RAG architecture" width="900">
  <br>
  <sub><b>Figure 1.</b> Local-first retrieval, evaluation, automation, and citation-aware generation.</sub>
</div>

> [!TIP]
> The complete pipeline explanation is available in the [Architecture guide](docs/base/02-architecture.md).

---

<div align="center">

**Transparent retrieval. Local generation. Reproducible RAG experiments.**

⭐ Star the repository if this project helps your work.

</div>