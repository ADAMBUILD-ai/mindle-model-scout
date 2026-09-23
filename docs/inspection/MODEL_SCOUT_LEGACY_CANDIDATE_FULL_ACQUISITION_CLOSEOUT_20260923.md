# MODEL SCOUT Legacy Candidate Full Acquisition Closeout

Date: 2026-09-23

PR: `#77` (`acquisition/legacy-candidates-full-20260923`)

## Outcome

The ten unacquired legacy model candidates were converted into ten permitted, immutable, locally verified model assets. Two original candidates that failed the license gate were rejected and replaced before acquisition.

`LEGACY_SCOUTED_MODEL_ACQUISITION: PASS`

## Totals

- Newly acquired and SHA-256 verified models: **10**
- Newly CPU runtime-tested models: **10**
- Actual weight bytes acquired: **7,528,707,580 bytes**
- Rejected originals: **2**
- Permitted replacements: **2**
- MODEL SCOUT model registry total: **13 ACQUIRED_VERIFIED models**

## License replacements

| Rejected original | Reason | Permitted replacement |
|---|---|---|
| `snunlp/KR-FinBert-SC` | License not exposed by source evidence | `Copycats/koelectra-base-v3-generalized-sentiment-analysis` — Apache-2.0 |
| `Salesforce/moirai-1.1-R-small` | CC BY-NC 4.0 is not permitted for commercial product adoption | `ibm-granite/granite-timeseries-ttm-r2` — Apache-2.0 |

## Verified models

1. `peyterho/financial-roberta-large-macro-sentiment`
2. `ENTUM-AI/FinBERT-Multi`
3. `BAAI/bge-m3`
4. `BAAI/bge-reranker-v2-m3`
5. `MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli`
6. `ibm-granite/granite-timeseries-ttm-r1`
7. `amazon/chronos-t5-small`
8. `microsoft/table-transformer-detection`
9. `Copycats/koelectra-base-v3-generalized-sentiment-analysis`
10. `ibm-granite/granite-timeseries-ttm-r2`

Every record contains an exact 40-character revision, actual downloaded files, exact byte sizes, per-file SHA-256, captured license metadata, and CPU output SHA-256. All runs used `trust_remote_code=False`.

## Runtime results

- Text classification/reranking: real logits generated.
- Embedding: real hidden-state tensor generated.
- Time-series models: real forecast/token logits generated.
- Table Transformer: real detection logits generated.
- Each output shape and SHA-256 is preserved under `evidence/runtime/`.

## Evidence

- `evidence/legacy-candidate-acquisition-20260923.json`
- `evidence/legacy-scouted-model-acquisition-closeout-20260923.json`
- `evidence/model-registry.json`
- `evidence/runtime/*.json`
- `scripts/acquire_legacy_candidates.py`
- `scripts/validate_legacy_candidate.py`

## Safety and storage

- No paid compute was used.
- No remote model code was executed.
- Only official Hugging Face repository files at exact revisions were downloaded.
- Approximately 3.9 GB of incomplete transient download-cache fragments were removed after successful acquisition. Verified model files were retained; removed fragments can be recreated by downloading again.

Product-specific financial benchmark approval remains a separate delivery gate and does not reduce the acquisition result.
