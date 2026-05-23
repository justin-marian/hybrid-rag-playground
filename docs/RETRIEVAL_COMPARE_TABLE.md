# Retrieval Comparison

Metrics are reported per retriever and dataset. Higher is better for all metrics.

| retriever   |   fiqa_recall@10 |   fiqa_mrr |   fiqa_ndcg@10 |   nfcorpus_recall@10 |   nfcorpus_mrr |   nfcorpus_ndcg@10 |   scifact_recall@10 |   scifact_mrr |   scifact_ndcg@10 |
|:------------|-----------------:|-----------:|---------------:|---------------------:|---------------:|-------------------:|--------------------:|--------------:|------------------:|
| bm25        |           0.2062 |     0.2051 |         0.1612 |               0.1254 |         0.4811 |             0.2537 |              0.7062 |        0.5786 |            0.6020 |
| dense       |           0.4418 |     0.4524 |         0.3753 |               0.1374 |         0.4959 |             0.2839 |              0.7854 |        0.6206 |            0.6559 |
| hybrid      |           0.4171 |     0.3920 |         0.3333 |               0.1407 |         0.5295 |             0.2912 |              0.7928 |        0.6480 |            0.6776 |
