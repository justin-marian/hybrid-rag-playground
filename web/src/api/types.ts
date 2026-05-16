export type RetrieverName = "bm25" | "dense" | "hybrid";

export interface Hit {
    rank: number;
    chunk_id: string;
    doc_id: string;
    title: string;
    text: string;
    score: number;
}

export interface DatasetInfo {
    key: string;
    name: string;
    split: string;
    description: string;
    expected_size: number;
    collection_name: string;
    indexed_count: number | null;
}

export interface DatasetsResponse {
    datasets: DatasetInfo[];
}

export interface HealthResponse {
    status: "ok" | "degraded";
    weaviate_ready: boolean;
    ollama_reachable: boolean;
    embedder_loaded: boolean;
    detail: string | null;
}

export interface ConfigResponse {
    embedding_model: string;
    default_retriever: RetrieverName;
    default_top_k: number;
    default_alpha: number;
    default_dataset: string;
    default_llm_model: string;
    available_datasets: string[];
}

export interface RetrieveRequest {
    query: string;
    dataset: string;
    retriever: RetrieverName;
    top_k: number;
    alpha?: number | null;
}

export interface RetrieveResponse {
    query: string;
    dataset: string;
    retriever: RetrieverName;
    top_k: number;
    alpha: number | null;
    hits: Hit[];
}

export interface RagRequest extends RetrieveRequest {
    model?: string | null;
}

export interface RagResponse extends RetrieveResponse {
    model: string;
    answer: string;
    prompt: string;
}
