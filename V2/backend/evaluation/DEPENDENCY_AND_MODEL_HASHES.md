# Pinned Dependencies and Model Provenance (T0.1 Baseline)

- **Timestamp**: 2026-10-25T04:09:20+05:30
- **Python Version**: 3.12.6 (Windows 64-bit)
- **Lockfile**: `V2/backend/requirements-nlp.lock`
  - **SHA-256**: `65f510a5f6736866db5baf0fa9e959e63221f9390ea2dd703f6c3a93322a4348`

## Key Packages
| Package | Version |
|---|---|
| fastapi | 0.128.0 |
| uvicorn | 0.40.0 |
| pydantic | 2.11.7 |
| sqlalchemy | 2.0.38 |
| spacy | 3.8.4 |
| en-core-web-sm | 3.8.0 |
| torch | 2.4.0+cu124 |
| transformers | 4.37.2 |
| tokenizers | 0.15.2 |
| scikit-learn | 1.6.1 |
| numpy | 1.26.4 |
| nltk | 3.9.1 |
| pytest | 9.0.2 |

## Model Checkpoints and Metadata
- **spaCy Model**: `en_core_web_sm` v3.8.0
  - Metadata hash (SHA-256): `ce1a214f8dc286e7a19440912afd7ab356d5cd20256ca271f28abbfa49376ac8`
- **Fallback NLP Parser**: Blank English with `sentencizer` (`sentence_fallback` pipeline)
- **Local Neural Model Cache**: `V2/backend/models/` (git-ignored, strictly local weights)
