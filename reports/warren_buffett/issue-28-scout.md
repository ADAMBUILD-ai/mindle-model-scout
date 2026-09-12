# Issue #28 — WARREN–BUFFETT Hugging Face Scout Report

- Checked: `2026-09-13T01:33:00+09:00`
- Status: **SCOUT_EVIDENCE_GENERATED_NOT_YET_MERGED**
- Method: live public Hugging Face model/dataset/Space page verification via current web search.
- Boundary: the repository CLI itself was **not** executed from this automation environment, so this report does not claim CLI-run provenance.

## License gate

- `LICENSE_PERMITTED`: MIT / Apache-2.0.
- `LICENSE_PERMITTED_WITH_ATTRIBUTION`: CC BY 4.0; attribution obligations remain.
- `LICENSE_REVIEW_REQUIRED`: license metadata missing/unclear; no auto-adoption.
- `LICENSE_NOT_PERMITTED`: non-commercial license for this commercial/internal product path; reject until scope/legal approval changes.

## Role mapping

### WAR-001 — Korea Market Agent

| Candidate | Type | License gate | Recommendation | Korean/local note |
|---|---|---|---|---|
| `snunlp/KR-FinBert-SC` | model | LICENSE_REVIEW_REQUIRED | REVIEW_REQUIRED | Korean finance sentiment; local Transformers; live page exposed no license |
| `BAAI/bge-m3` | model | LICENSE_PERMITTED | RECOMMENDED | multilingual retrieval incl. Korean/English; local |
| `peyterho/financial-roberta-large-macro-sentiment` | model | LICENSE_PERMITTED | RECOMMENDED | English macro/policy sentiment; local |

Use KR-FinBert-SC only after license review; BGE-M3 for bilingual retrieval; macro RoBERTa for English/global policy context.

### WAR-002 — Supply & Money Flow Agent

| Candidate | Type | License gate | Recommendation | Note |
|---|---|---|---|---|
| `ibm-granite/granite-timeseries-ttm-r1` | model | LICENSE_PERMITTED | RECOMMENDED | tiny multivariate forecaster; CPU/laptop feasible |
| `amazon/chronos-t5-small` | model | LICENSE_PERMITTED | RECOMMENDED | probabilistic time-series foundation model |
| `Salesforce/moirai-1.1-R-small` | model | LICENSE_NOT_PERMITTED | REJECT | CC BY-NC 4.0; benchmark only |

### WAR-003 — US & Global Market Agent

| Candidate | Type | License gate | Recommendation | Note |
|---|---|---|---|---|
| `peyterho/financial-roberta-large-macro-sentiment` | model | LICENSE_PERMITTED | RECOMMENDED | macro/central-bank/policy tone |
| `amazon/chronos-t5-small` | model | LICENSE_PERMITTED | RECOMMENDED | rates/FX/index forecasting research |
| `ibm-granite/granite-timeseries-ttm-r1` | model | LICENSE_PERMITTED | RECOMMENDED | lightweight multivariate series research |

### WAR-004 — News & Catalyst Agent

| Candidate | Type | License gate | Recommendation | Note |
|---|---|---|---|---|
| `ENTUM-AI/FinBERT-Multi` | model | LICENSE_PERMITTED | RECOMMENDED | finance-news sentiment; Apache-2.0 |
| `BAAI/bge-m3` | model | LICENSE_PERMITTED | RECOMMENDED | multilingual retrieval/embedding |
| `BAAI/bge-reranker-v2-m3` | model | LICENSE_PERMITTED | RECOMMENDED | multilingual cross-encoder reranking |
| `trismik/fpb-fiqasa` | dataset | LICENSE_PERMITTED_WITH_ATTRIBUTION | RECOMMENDED | finance sentiment regression benchmark |

### WAR-005 — Quant & Momentum Scout

| Candidate | Type | License gate | Recommendation | Note |
|---|---|---|---|---|
| `ibm-granite/granite-timeseries-ttm-r1` | model | LICENSE_PERMITTED | RECOMMENDED | primary lightweight quant candidate |
| `amazon/chronos-t5-small` | model | LICENSE_PERMITTED | RECOMMENDED | probabilistic forecasting candidate |
| `ArnabDeo/ai-stock-predictor` | space | LICENSE_PERMITTED | REVIEW_REQUIRED | MIT demo using Chronos & Moirai; dependency audit required |

### GATE-001 — Verification Agent

| Candidate | Type | License gate | Recommendation | Note |
|---|---|---|---|---|
| `MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli` | model | LICENSE_PERMITTED | RECOMMENDED | NLI contradiction/evidence-consistency |
| `BAAI/bge-reranker-v2-m3` | model | LICENSE_PERMITTED | RECOMMENDED | evidence ordering/reranking |
| `BAAI/bge-m3` | model | LICENSE_PERMITTED | RECOMMENDED | multilingual evidence retrieval |

### BUF-001 — Value & Quality

| Candidate | Type | License gate | Recommendation | Note |
|---|---|---|---|---|
| `Mr-Rosen/Accuracy-Is-Not-Enough-FinQA-Dataset` | dataset | LICENSE_PERMITTED_WITH_ATTRIBUTION | RECOMMENDED | long-context financial QA / numerical reasoning |
| `microsoft/table-transformer-detection` | model | LICENSE_PERMITTED | RECOMMENDED | financial-report table detection |
| `BAAI/bge-m3` | model | LICENSE_PERMITTED | RECOMMENDED | multilingual financial-document retrieval |

### BUF-002 — Quant

| Candidate | Type | License gate | Recommendation | Note |
|---|---|---|---|---|
| `ibm-granite/granite-timeseries-ttm-r1` | model | LICENSE_PERMITTED | RECOMMENDED | lightweight multivariate forecasting |
| `amazon/chronos-t5-small` | model | LICENSE_PERMITTED | RECOMMENDED | probabilistic forecasting |
| `Salesforce/moirai-1.1-R-small` | model | LICENSE_NOT_PERMITTED | REJECT | NC license blocks adoption |

### BUF-003 — Market Regime

| Candidate | Type | License gate | Recommendation | Note |
|---|---|---|---|---|
| `ibm-granite/granite-timeseries-ttm-r1` | model | LICENSE_PERMITTED | RECOMMENDED | numeric regime features |
| `amazon/chronos-t5-small` | model | LICENSE_PERMITTED | RECOMMENDED | numeric regime/forecast features |
| `peyterho/financial-roberta-large-macro-sentiment` | model | LICENSE_PERMITTED | RECOMMENDED | macro/policy text regime context |

### BUF-004 — Catalyst & Timing

| Candidate | Type | License gate | Recommendation | Note |
|---|---|---|---|---|
| `ENTUM-AI/FinBERT-Multi` | model | LICENSE_PERMITTED | RECOMMENDED | catalyst tone |
| `peyterho/financial-roberta-large-macro-sentiment` | model | LICENSE_PERMITTED | RECOMMENDED | macro/policy catalyst context |
| `BAAI/bge-reranker-v2-m3` | model | LICENSE_PERMITTED | RECOMMENDED | evidence prioritization |
| `trismik/fpb-fiqasa` | dataset | LICENSE_PERMITTED_WITH_ATTRIBUTION | RECOMMENDED | sentiment regression benchmark |

### BUF-005 — Risk Officer

| Candidate | Type | License gate | Recommendation | Note |
|---|---|---|---|---|
| `MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli` | model | LICENSE_PERMITTED | RECOMMENDED | contradiction/evidence check only |
| `peyterho/financial-roberta-large-macro-sentiment` | model | LICENSE_PERMITTED | RECOMMENDED | explanatory macro-risk text signal |
| `Mr-Rosen/Accuracy-Is-Not-Enough-FinQA-Dataset` | dataset | LICENSE_PERMITTED_WITH_ATTRIBUTION | RECOMMENDED | financial reasoning evaluation |

Deterministic Core remains the final risk gate; model output is advisory only.

## Verified catalog

### `snunlp/KR-FinBert-SC`
- Type/revision: model / `main`
- License: not exposed on the live page → **LICENSE_REVIEW_REQUIRED**
- Language: Korean
- Runtime: BERT-class; GPU preferred, CPU possible
- Evidence: Korean financial corpus includes economic news and analyst reports; 39 likes observed.
- Warning: no auto-adoption until license metadata is verified.
- Source: https://huggingface.co/snunlp/KR-FinBert-SC

### `peyterho/financial-roberta-large-macro-sentiment`
- Type/revision: model / `main`
- License: Apache-2.0 → **LICENSE_PERMITTED**
- Language: English
- Runtime: 355M params; model card notes ~1.5GB GPU memory and higher latency than FinBERT.
- Fit: finance/macro/policy/central-bank sentiment.
- Warning: 128-token fine-tuning length; chunk long documents.
- Source: https://huggingface.co/peyterho/financial-roberta-large-macro-sentiment

### `ENTUM-AI/FinBERT-Multi`
- Type/revision: model / `a061e93fec562163f71aa10fad8e3d1917785c67`
- License: Apache-2.0 → **LICENSE_PERMITTED**
- Language: English
- Runtime: ~0.1B params / 438MB safetensors; 9 downloads last month observed.
- Fit: finance sentiment trained across five finance datasets.
- Source: https://huggingface.co/ENTUM-AI/FinBERT-Multi

### `BAAI/bge-m3`
- Type/revision: model / `e1f456861c4ba62db1cf7fc31093d04e66b5040f`
- License: MIT → **LICENSE_PERMITTED**
- Language: multilingual
- Runtime: ~2.27GB safetensors; GPU recommended for throughput; ~3.49k likes observed.
- Fit: multilingual dense/sparse/multi-vector retrieval; Korean-English evidence retrieval.
- Source: https://huggingface.co/BAAI/bge-m3

### `BAAI/bge-reranker-v2-m3`
- Type/revision: model / `main`
- License: Apache-2.0 → **LICENSE_PERMITTED**
- Language: multilingual
- Runtime: ~0.6B params; ~18.2M downloads last month observed.
- Fit: cross-encoder reranking/evidence prioritization.
- Source: https://huggingface.co/BAAI/bge-reranker-v2-m3

### `MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli`
- Type/revision: model / `e5350efffb6dea3ad0962eafd0bc0b9e212a9ff8`
- License: MIT → **LICENSE_PERMITTED**
- Language: English
- Runtime: ~371MB checkpoint; local Transformers.
- Fit: MNLI/FEVER/ANLI NLI for contradiction/evidence consistency.
- Warning: verification aid, not deterministic truth oracle.
- Source: https://huggingface.co/MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli

### `ibm-granite/granite-timeseries-ttm-r1`
- Type/revision: model / `e23db1e65d1f58f91e2996ead108617f8a12b8e5`
- License: Apache-2.0 → **LICENSE_PERMITTED**
- Runtime: ~805K params; CPU/laptop feasible; 23,608 downloads last month observed.
- Fit: lightweight multivariate forecasting for quant/regime/money-flow experiments.
- Warning: R1 model card emphasizes minutely/hourly resolutions; daily/weekly stock use needs validation or newer variants.
- Source: https://huggingface.co/ibm-granite/granite-timeseries-ttm-r1

### `amazon/chronos-t5-small`
- Type/revision: model / `ff3aecf0fcd6faa10346dbd3162c18f720cc3bb2`
- License: Apache-2.0 → **LICENSE_PERMITTED**
- Runtime: ~185MB checkpoint; local Chronos package; GPU recommended.
- Fit: probabilistic time-series forecasting for price/volume/macro experiments.
- Warning: forecasting output is not a trading signal; require walk-forward/leakage-safe evaluation.
- Source: https://huggingface.co/amazon/chronos-t5-small

### `Salesforce/moirai-1.1-R-small`
- Type/revision: model / `main`
- License: CC BY-NC 4.0 → **LICENSE_NOT_PERMITTED / REJECT**
- Runtime: 13.8M params; 48,118 downloads last month observed.
- Fit: technically useful benchmark only.
- Source: https://huggingface.co/Salesforce/moirai-1.1-R-small

### `microsoft/table-transformer-detection`
- Type/revision: model / `main`
- License: MIT → **LICENSE_PERMITTED**
- Fit: table detection from financial reports before OCR/structure extraction.
- Warning: detection only; downstream table structure/OCR still required.
- Source: https://huggingface.co/microsoft/table-transformer-detection

### `Mr-Rosen/Accuracy-Is-Not-Enough-FinQA-Dataset`
- Type/revision: dataset / `main`
- License: CC BY 4.0 → **LICENSE_PERMITTED_WITH_ATTRIBUTION**
- Size: ~9,200 rows / ~448MB; 75 downloads last month observed.
- Fit: long-context numerical reasoning over financial tables/text.
- Source: https://huggingface.co/datasets/Mr-Rosen/Accuracy-Is-Not-Enough-FinQA-Dataset

### `trismik/fpb-fiqasa`
- Type/revision: dataset / `main`
- License: CC BY 4.0 → **LICENSE_PERMITTED_WITH_ATTRIBUTION**
- Size: 2,159 rows / ~298KB; 32 downloads last month observed.
- Fit: compact Financial PhraseBank + FiQA sentiment benchmark.
- Source: https://huggingface.co/datasets/trismik/fpb-fiqasa

### `ArnabDeo/ai-stock-predictor`
- Type/revision: Space / `8d797b3`
- License: MIT → Space itself **LICENSE_PERMITTED**
- Fit: Gradio reference app using Chronos & Moirai.
- Recommendation: **REVIEW_REQUIRED** because its dependency chain includes Moirai, whose model license is non-commercial.
- Source: https://huggingface.co/spaces/ArnabDeo/ai-stock-predictor

## Watch/snapshot proposal

- Identity: `resource_type + repository_id + revision`.
- Active shortlist: daily snapshot; benchmark-only resources: weekly.
- Track: revision, license metadata, downloads/likes, availability/gating, recommendation state.
- Alert on: license changes, deletion/gating, new revision, recommendation-state change, large popularity changes.

## Acceptance boundary

- 11/11 requested roles are mapped.
- Model, dataset and Space resources are represented.
- License gate is applied; NC and unknown-license candidates are not auto-selected.
- This is verified live lookup Evidence generation. **Do not close Issue #28 until PR CI passes and the report is merged/referenced from the Issue.**
