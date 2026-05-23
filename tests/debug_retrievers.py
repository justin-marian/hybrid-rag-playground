from src.embeddings.minilm_embedder import MiniLMEmbedder
from src.retrieval.bm25 import BM25Retriever
from src.retrieval.dense import DenseRetriever
from src.retrieval.hybrid import HybridRetriever
from src.utils.io import load_yaml
from src.weaviate_io.client import weaviate_client
from src.weaviate_io.schema import collection_name

cfg = load_yaml("configs/retrieval.yaml")
dataset = "scifact"
query = "Does aspirin reduce the risk of heart disease?"

name = collection_name(cfg["weaviate"]["collection_prefix"], dataset)
embedder = MiniLMEmbedder(**cfg["embedding"])

with weaviate_client(host=cfg["weaviate"]["host"], http_port=cfg["weaviate"]["http_port"], grpc_port=cfg["weaviate"]["grpc_port"]) as client:
    retrievers = [
        BM25Retriever(client, name),
        DenseRetriever(client, name, embedder),
        HybridRetriever(client, name, embedder, alpha=0.0),
        HybridRetriever(client, name, embedder, alpha=0.5),
        HybridRetriever(client, name, embedder, alpha=1.0)]

    for retriever in retrievers:
        print("\n===", retriever.name, getattr(retriever, "alpha", "") , "===")
        hits = retriever.search(query, top_k=10)

        for hit in hits:
            print(hit.rank, hit.score, hit.doc_id, hit.chunk_id)
