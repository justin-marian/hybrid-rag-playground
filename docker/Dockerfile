# Optional Dockerfile, NOT required to run the project.
# The recommended workflow is:
#   - run Weaviate via docker-compose
#   - run Ollama natively on the host
#   - run the Python code in a host venv
#
# This image exists only for users who want to run the Python pipeline inside a container
# alongside Weaviate. In that case, set OLLAMA_HOST to host.docker.internal:11434.

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /hybrid-rag-beir

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential git curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml setup.py README.md ./
COPY src ./src
COPY configs ./configs

RUN pip install --upgrade pip \
    && pip install -e .

CMD ["bash"]
