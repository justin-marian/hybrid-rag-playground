# Hybrid RAG Evaluation Report

This report summarizes retrieval quality, calibration behavior, sample RAG traces, and the hyperparameters used to obtain the results.

## Input artifacts

- Retrieval metrics: `/mnt/d/__FACULTATE ACS__/Master/DMDA/HW2/data/results/retrieval_metrics.csv`
- Sweep results: `/mnt/d/__FACULTATE ACS__/Master/DMDA/HW2/data/results/sweep_results.csv`
- RAG demo traces: `/mnt/d/__FACULTATE ACS__/Master/DMDA/HW2/data/results/rag/rag_demo.json`
- Retrieval config: `/mnt/d/__FACULTATE ACS__/Master/DMDA/HW2/configs/retrieval.yaml`
- RAG config: `/mnt/d/__FACULTATE ACS__/Master/DMDA/HW2/configs/rag.yaml`
- Dataset config: `/mnt/d/__FACULTATE ACS__/Master/DMDA/HW2/configs/datasets.yaml`
- Auto research config: `/mnt/d/__FACULTATE ACS__/Master/DMDA/HW2/configs/auto_research.yml`

## Hyperparameters from configuration files

Configured hyperparameter names and values available when the report was generated.

| source         | hyperparameter          | value                                  | meaning                                                              |
|:---------------|:------------------------|:---------------------------------------|:---------------------------------------------------------------------|
| retrieval.yaml | embedding.model_name    | sentence-transformers/all-MiniLM-L6-v2 | Embedding model used by dense and hybrid retrieval.                  |
| retrieval.yaml | retrieval.top_k         | 10                                     | Number of retrieved chunks/documents evaluated per query.            |
| retrieval.yaml | retrieval.hybrid_alpha  | 0.5                                    | Hybrid retrieval blend weight.                                       |
| retrieval.yaml | retrieval.target_vector | default                                | Weaviate target vector name.                                         |
| rag.yaml       | rag.dataset             | scifact                                | Default dataset used by the RAG pipeline.                            |
| rag.yaml       | rag.retriever           | hybrid                                 | Default retriever used by the RAG pipeline.                          |
| rag.yaml       | rag.top_k               | 10                                     | Default number of hits used by generation.                           |
| rag.yaml       | rag.max_chunk_chars     | 1200                                   | Maximum characters copied from each retrieved chunk into the prompt. |
| rag.yaml       | llm.provider            | ollama                                 | LLM provider used for generation.                                    |
| rag.yaml       | llm.model               | llama3.1:8b                            | LLM model used for generation.                                       |
| rag.yaml       | llm.host                | http://localhost:11434                 | LLM host endpoint.                                                   |

## Hyperparameters recorded in result artifacts

Which hyperparameter columns are stored together with the metrics.

| artifact              | recorded_hyperparameters        | missing_recommended_hyperparameters                                                                                                                             |
|:----------------------|:--------------------------------|:----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| retrieval_metrics.csv | dataset, retriever, num_queries | top_k, alpha, hybrid_alpha, embedding_model, target_vector, chunk_size, chunk_overlap, max_chunk_chars, bm25_k1, bm25_b, split                                  |
| sweep_results.csv     | none                            | dataset, retriever, top_k, alpha, hybrid_alpha, embedding_model, target_vector, chunk_size, chunk_overlap, max_chunk_chars, bm25_k1, bm25_b, split, num_queries |

## Run-level results with recorded hyperparameters

Available hyperparameters shown next to the reported metrics.

| dataset   | retriever   |   num_queries |   recall@10 |    mrr |   ndcg@10 |
|:----------|:------------|--------------:|------------:|-------:|----------:|
| nfcorpus  | bm25        |           323 |      0.1254 | 0.4811 |    0.2537 |
| nfcorpus  | dense       |           323 |      0.1337 | 0.4879 |    0.2789 |
| nfcorpus  | hybrid      |           323 |      0.1450 | 0.5358 |    0.2996 |
| scifact   | bm25        |           300 |      0.7062 | 0.5786 |    0.6020 |
| scifact   | dense       |           300 |      0.7854 | 0.6206 |    0.6559 |
| scifact   | hybrid      |           300 |      0.7725 | 0.6318 |    0.6623 |
| fiqa      | bm25        |           648 |      0.2062 | 0.2051 |    0.1612 |
| fiqa      | dense       |           648 |      0.4418 | 0.4524 |    0.3752 |
| fiqa      | hybrid      |           648 |      0.3851 | 0.3707 |    0.3052 |

## Retrieval summary

Average retrieval metrics by retriever. Higher values are better.

| retriever   |   recall@10 |    mrr |   ndcg@10 |
|:------------|------------:|-------:|----------:|
| dense       |      0.4536 | 0.5203 |    0.4367 |
| hybrid      |      0.4342 | 0.5128 |    0.4224 |
| bm25        |      0.3459 | 0.4216 |    0.3390 |

## Best retriever per dataset

Best rows are selected by `ndcg@10`, because it captures top-rank quality.

| retriever   | dataset   |   num_queries |   recall@10 |   ndcg@10 |    mrr |
|:------------|:----------|--------------:|------------:|----------:|-------:|
| dense       | fiqa      |           648 |      0.4418 |    0.3752 | 0.4524 |
| hybrid      | nfcorpus  |           323 |      0.1450 |    0.2996 | 0.5358 |
| hybrid      | scifact   |           300 |      0.7725 |    0.6623 | 0.6318 |

## Calibration highlights

Top sweep rows sorted by the strongest available ranking metric.

_No data available._

## RAG trace samples

Compact view of saved RAG demo traces. Use the JSON artifact for full details.

|   query_id | dataset   | retriever   |   top_k | alpha   | model   |   num_hits | answer_preview                                                                                                                                                                          |   prompt_chars |
|-----------:|:----------|:------------|--------:|:--------|:--------|-----------:|:----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------:|
|          1 | scifact   | hybrid      |       5 |         |         |          5 | **Answer:** 0-dimensional biomaterials show inductive properties [29638116::doc].  - **Main finding:** Complex tissue and disease modeling using human-induced pluripotent stem cell... |          10761 |
|          3 | scifact   | hybrid      |       5 |         |         |          5 | **Answer:** The 1,000 genomes project enables mapping of genetic sequence variation consisting of rare variants with larger penetrance effects than common variants [2739854::doc]. ... |          10385 |
|          5 | scifact   | hybrid      |       5 |         |         |          5 | **Answer:** 1/2000 people in the UK have abnormal PrP positivity [13734012::doc].  - **Main finding:** The prevalence of abnormal prion protein in human appendixes after the bovine... |           9485 |
|         13 | scifact   | hybrid      |       5 |         |         |          5 | **Answer:** 5% of perinatal mortality is due to low birth weight [1263446::part_001].  - **Main finding:** The perinatal mortality rate was 69 per 1000 births, and the rate of stil... |          10611 |
|         36 | scifact   | hybrid      |       5 |         |         |          5 | **Answer:** A deficiency of vitamin B12 increases blood levels of homocysteine [33409100::part_000].  - **Main finding:** High plasma homocysteine levels are a risk factor for mort... |          11529 |

## Recommended hyperparameters to store in every experiment CSV

- `dataset`: BEIR dataset key, for example `nfcorpus`, `scifact`, or `fiqa`.
- `retriever`: retrieval mode, for example `bm25`, `dense`, or `hybrid`.
- `top_k`: number of retrieved candidates used for evaluation.
- `alpha` or `hybrid_alpha`: dense/sparse interpolation weight used by hybrid retrieval.
- `embedding_model`: sentence-transformer or embedding model used by dense retrieval.
- `target_vector`: Weaviate target vector name.
- `chunk_size` and `chunk_overlap`: chunking parameters used before indexing.
- `bm25_k1` and `bm25_b`: BM25 scoring parameters, if customized.
- `split`: dataset split evaluated.
- `num_queries`: number of evaluated queries.

## How to read this report

- Start with retrieval metrics before judging generated answers.
- Low Recall@10 means relevant documents are missing.
- Low MRR means useful evidence appears too late.
- Low nDCG@10 means ranking quality needs tuning.
- If a hyperparameter is listed as missing, the current result artifact did not record it and the value must be taken from the config files or experiment command.
