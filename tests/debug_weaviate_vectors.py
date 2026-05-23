from src.utils.io import load_yaml
from src.weaviate_io.client import weaviate_client
from src.weaviate_io.schema import collection_name

cfg = load_yaml("configs/retrieval.yaml")

for dataset in ["scifact", "nfcorpus", "fiqa"]:
    name = collection_name(cfg["weaviate"]["collection_prefix"], dataset)

    with weaviate_client(host=cfg["weaviate"]["host"], http_port=cfg["weaviate"]["http_port"], grpc_port=cfg["weaviate"]["grpc_port"]) as client:
        collection = client.collections.get(name)
        response = collection.query.fetch_objects(limit=3, include_vector=True)

        print("\nCOLLECTION:", name)
        print("objects:", len(response.objects))

        for obj in response.objects:
            vector = obj.vector
            props = obj.properties or {}

            print("doc_id:", props.get("doc_id"))
            print("chunk_id:", props.get("chunk_id"))

            if vector is None:
                print("VECTOR: None")
            elif isinstance(vector, dict):
                print("VECTOR dict keys:", vector.keys())
                print("VECTOR length:", {k: len(v) for k, v in vector.items()})
            else:
                print("VECTOR length:", len(vector))
