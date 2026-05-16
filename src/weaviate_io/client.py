"""Weaviate v4 local connection helpers."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

import weaviate
from weaviate.connect import ConnectionParams

from src.utils.logging import get_logger

logger = get_logger(__name__)


def connection_params(host: str, http_port: int, grpc_port: int) -> ConnectionParams:
    """Build local non-TLS Weaviate connection parameters."""
    return ConnectionParams.from_params(
        http_host=host, http_port=http_port, http_secure=False,
        grpc_host=host, grpc_port=grpc_port, grpc_secure=False)


def not_ready_message(host: str, http_port: int) -> str:
    """Return the startup hint shown when Weaviate is unreachable or not ready."""
    return f"Weaviate is not ready at http://{host}:{http_port}. Did you run `docker compose -f docker/docker-compose.yml up -d`?"


def connect_local(host: str = "localhost", http_port: int = 8080, grpc_port: int = 50051) -> weaviate.WeaviateClient:
    """Open a local Weaviate connection and verify readiness."""
    client = weaviate.WeaviateClient(connection_params=connection_params(host, http_port, grpc_port))
    client.connect()

    if client.is_ready():
        logger.info("Connected to Weaviate at %s:%d (gRPC %d)", host, http_port, grpc_port)
        return client

    client.close()
    raise RuntimeError(not_ready_message(host, http_port))


@contextmanager
def weaviate_client(host: str = "localhost", http_port: int = 8080, grpc_port: int = 50051) -> Iterator[weaviate.WeaviateClient]:
    """Yield a context-managed Weaviate client and always close it."""
    client = connect_local(host=host, http_port=http_port, grpc_port=grpc_port)
    try:
        yield client
    finally:
        client.close()
