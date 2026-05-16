# Running environment

Reference values for the environment the project was developed against.

| Component         | Version / value                                |
|-------------------|-------------------------------------------------|
| OS                | Linux / macOS / WSL2 on Windows                |
| Python            | 3.10+ (tested with 3.11)                       |
| Docker            | 24+                                            |
| Weaviate          | `cr.weaviate.io/semitechnologies/weaviate:1.27.0` |
| Ollama            | 0.3+                                           |
| LLM (default)     | `gemma2:2b`                                    |
| LLM (16 GB option)| `llama3.2:3b`                                  |
| Embedder          | `sentence-transformers/all-MiniLM-L6-v2`       |
| weaviate-client   | `>=4.7,<5.0` (v4 Python client)                |
| Hardware (min.)   | 8 GB RAM, ~10 GB free disk, CPU only           |

Ports used:
- `8080`: Weaviate REST
- `50051`: Weaviate gRPC
- `11434`: Ollama
