# RAG Manual Evaluation

**Dataset:** scifact  
**Retriever:** hybrid  
**Top-k:** 5  
**Queries:** 10

_Use this table during manual evaluation. Mark each row as_ `correct`, `partial`, or `hallucination` _and note the cited chunks._

| # | Query | Top chunks (chunk_id) | LLM answer (truncated) | Notes |
|---|---|---|---|---|
| 1 | 0-dimensional biomaterials show inductive properties. | 10608397::doc, 10906636::doc, 43385013::doc | The provided text does not contain information about whether 0-dimensional biomaterials show inductive properties.  Insufficient context. |   |
| 2 | 1,000 genomes project enables mapping of genetic sequence variation consisting of rare variants with… | 2739854::doc, 23389795::doc, 14717500::doc | Rare variants create synthetic genome-wide associations. [chunk_id=43334921::part_001] |   |
| 3 | 1/2000 in UK have abnormal PrP positivity. | 13734012::doc, 42240424::doc, 17333231::doc | 1/2000 in UK have abnormal PrP positivity [17333231::doc]. |   |
| 4 | 5% of perinatal mortality is due to low birth weight. | 1263446::part_001, 7662395::doc, 34544514::part_001 | 5% of perinatal mortality is linked to low birth weight [1263446::part_001]. |   |
| 5 | A deficiency of vitamin B12 increases blood levels of homocysteine. | 42441846::doc, 33409100::part_000, 9555784::part_001 | A deficiency of vitamin B12 increases blood levels of homocysteine [33409100::part_001]. |   |
| 6 | A high microerythrocyte count raises vulnerability to severe anemia in homozygous alpha (+)- thalass… | 18174210::part_001, 18174210::part_000, 40913091::doc | A high microerythrocyte count raises vulnerability to severe anemia in homozygous alpha (+)- thalassemia trait subjects [18174210::part_001]. |   |
| 7 | A total of 1,000 people in the UK are asymptomatic carriers of vCJD infection. | 18617259::doc, 9394119::part_000, 11880289::part_000 | 1000 people in the UK are asymptomatic carriers of vCJD infection [chunk_id=18617259::doc]. |   |
| 8 | ADAR1 binds to Dicer to cleave pre-miRNA. | 5953485::doc, 5702790::doc, 7029990::doc | ADAR1 binds to Dicer to cleave pre-miRNA [5953485::doc]. |   |
| 9 | AIRE is expressed in some skin tumors. | 12580014::doc, 39559521::doc, 18488986::doc | AIRE is expressed in some skin tumors [12580014::doc].  Aire deficiency promotes TRP-1-specific immune rejection of melanoma [25738896::doc]. |   |
| 10 | ALDH1 expression is associated with better breast cancer outcomes. | 45638119::doc, 8963413::doc, 2140497::part_001 | ALDH1 expression is associated with better breast cancer outcomes [2140497::part_001]. |   |
