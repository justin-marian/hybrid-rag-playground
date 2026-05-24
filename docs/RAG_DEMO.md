# RAG Manual Evaluation

**Dataset:** scifact  
**Retriever:** hybrid  
**Top-k:** 5  
**Queries:** 5

_Use this table during manual evaluation. Mark each row as_ `correct`, `partial`, or `hallucination` _and note the cited chunks._

| # | Query | Top chunks (chunk_id) | LLM answer (truncated) | Notes |
|---|---|---|---|---|
| 1 | 0-dimensional biomaterials show inductive properties. | 803312::doc, 10608397::doc, 29638116::doc | **Answer:** 0-dimensional biomaterials show inductive properties [29638116::doc].  - **Main finding:** Complex tissue and disease modeling using human-induced pluripotent stem cells (hiPSCs) has been explored, but the context does not directly address the inductive properties of … |   |
| 2 | 1,000 genomes project enables mapping of genetic sequence variation consisting of rare variants with… | 2739854::doc, 23389795::doc, 14717500::doc | **Answer:** The 1,000 genomes project enables mapping of genetic sequence variation consisting of rare variants with larger penetrance effects than common variants [2739854::doc].  - **Main finding:** Rare variants can have larger penetrance effects than common variants [2739854:… |   |
| 3 | 1/2000 in UK have abnormal PrP positivity. | 13734012::doc, 18340282::part_001, 18617259::doc | **Answer:** 1/2000 people in the UK have abnormal PrP positivity [13734012::doc].  - **Main finding:** The prevalence of abnormal prion protein in human appendixes after the bovine spongiform encephalopathy epizootic was 493 per million population (95% confidence interval 282 to … |   |
| 4 | 5% of perinatal mortality is due to low birth weight. | 1263446::part_001, 7662395::doc, 8842332::part_001 | **Answer:** 5% of perinatal mortality is due to low birth weight [1263446::part_001].  - **Main finding:** The perinatal mortality rate was 69 per 1000 births, and the rate of stillbirth was 24 per 1000 births [7662395::doc]. - **Details:** Low birth weight and short birth interv… |   |
| 5 | A deficiency of vitamin B12 increases blood levels of homocysteine. | 33409100::part_000, 18557974::doc, 42441846::doc | **Answer:** A deficiency of vitamin B12 increases blood levels of homocysteine [33409100::part_000].  - **Main finding:** High plasma homocysteine levels are a risk factor for mortality and vascular disease in observational studies of patients with chronic kidney disease [3340910… |   |
