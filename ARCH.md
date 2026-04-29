# Architecture: Project Sheng V1

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        SHENG-NATIVE STACK                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   SCRAPER    │───▶│  TOKENIZER   │───▶│   PIPELINE   │      │
│  │  (Collect)   │    │ (Normalize)  │    │  (Orchestrate)│      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                   │                   │                │
│         ▼                   ▼                   ▼                │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   X/TikTok   │    │    SLANG     │    │   DATASET    │      │
│  │     API      │    │  DICTIONARY  │    │   EXPORT     │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. ShengScraper

**Purpose**: Rate-limited data collection from social media

**Key Classes**:
- `ShengPost`: Dataclass for scraped content
- `RateLimiter`: Token bucket rate limiting
- `ShengScraper`: Main scraper with platform abstraction

**Target Hashtags**:
```python
["sheng", "nairobian", "mbogigenje", "254", 
 "nairobilife", "shengword", "kenyantrends"]
```

**Output Format** (JSONL):
```json
{
  "id": "x_sheng_001",
  "platform": "x",
  "text": "Hii mbogi ni fiti sana!",
  "author": "user_1234",
  "timestamp": "2026-04-29T12:00:00",
  "engagement_score": 45,
  "hashtags": ["sheng", "nairobi"]
}
```

### 2. ShengTokenizer

**Purpose**: NLP preprocessing with Sheng-specific rules

**Processing Pipeline**:
```
Raw Text
    ↓
[Normalize Repeated Chars]  "soooo" → "soo"
    ↓
[Normalize Informal Spellings]  "xaxa" → "haha"
    ↓
[Slang Standardization]  "ronga" → "rongai"
    ↓
[Tokenization]  Split into tokens
    ↓
[Code-Switching Detection]  Tag language boundaries
    ↓
[Contextual Sentiment]  Apply Sheng-specific rules
    ↓
TokenizedOutput
```

**Key Features**:
- **Slang Mappings**: 75+ normalized forms
- **Contextual Sentiment**: Rules for ambiguous terms
  - "kudunda": default negative, positive in party context
  - "noma": default negative, positive as intensifier
- **Code-Switching Detection**: Identifies Swahili/English/Sheng boundaries

**Output**:
```python
TokenizedOutput(
    original_text="Buda hana chapaa",
    normalized_text="buda hana chapaa",
    tokens=["buda", "hana", "chapaa"],
    slang_terms=["buda", "chapaa"],
    code_switches=[],
    sentiment_score=-0.3,
    sentiment_label="negative",
    metadata={"token_count": 3, "slang_count": 2}
)
```

### 3. ShengPipeline

**Purpose**: End-to-end orchestration

**Workflow**:
```
Input: hashtag
    ↓
Scraper.collect() → List[ShengPost]
    ↓
Tokenizer.batch_tokenize() → List[TokenizedOutput]
    ↓
Enrich with metadata
    ↓
Export: training_data.jsonl
```

**Export Format** (LLM Training):
```json
{
  "text": "buda hana chapaa amekudunda",
  "metadata": {
    "sentiment": "negative",
    "sentiment_score": -0.6,
    "slang_terms": ["buda", "chapaa", "kudunda"],
    "code_switches": [],
    "original_text": "Buda hana chapaa, amekudunda",
    "platform": "x",
    "timestamp": "2026-04-29T12:00:00"
  }
}
```

## Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                        DATA LIFECYCLE                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  SOCIAL MEDIA ──▶ RAW JSONL ──▶ PROCESSED JSONL ──▶ MODEL  │
│     (X/TikTok)      (sheng_data_*.jsonl)  (training_*.jsonl)  │
│                                                              │
│  Fields:            Fields:                Fields:           │
│  - id               - post_id              - text            │
│  - text             - platform             - metadata        │
│  - author           - tokenized            - sentiment         │
│  - timestamp        - sentiment            - slang_terms       │
│  - hashtags                                          │
│  - engagement                                              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Dictionary Schema

```json
{
  "metadata": {
    "name": "Sheng-Native Dictionary v0.1",
    "created": "2026-04-29",
    "dialect": "Nairobi Sheng",
    "total_entries": 75
  },
  "slang_mappings": {
    "ronga": "rongai",
    "dem": "dame",
    "chapaa": "chapaa",
    ...
  },
  "contextual_sentiment": {
    "kudunda": {
      "default": "negative",
      "contexts": {
        "party": "positive",
        "dance": "positive",
        "fail": "negative"
      }
    }
  },
  "code_switching_patterns": {
    "sheng_english": ["na", "kwa", "ya", "wa", "za"],
    "sheng_swahili": ["sana", "tu", "pia", "tena"]
  }
}
```

## Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| Tokenization Speed | >1000 posts/sec | TBD |
| Slang Detection | >90% accuracy | TBD |
| Sentiment Accuracy | >85% vs GPT-4 | TBD |
| Dictionary Coverage | 75+ terms | 75 |

## Future Extensions

### Sheng-Native API (Service Layer)
```
POST /api/v1/tokenize
{
  "text": "Hii mbogi ni fiti",
  "options": {
    "return_slang": true,
    "sentiment_analysis": true
  }
}

Response:
{
  "normalized": "hii mbogi ni fiti",
  "tokens": [...],
  "slang": ["mbogi", "fiti"],
  "sentiment": "positive",
  "confidence": 0.89
}
```

### Boda-Pulse Integration
- GPS data from boda-boda riders
- Temporal geography mapping
- "Unmapped Insurance" risk scoring

### Chama-Chain Protocol
- Blockchain-based Chama contribution tracking
- Verifiable credit scores from informal savings
- Fractional asset ownership platform

## Development Standards

### Code Quality
- **Type Hints**: All functions annotated
- **Docstrings**: Google style
- **Commits**: Conventional format
  - `feat(nlp): add slang tokenizer`
  - `fix(scraper): handle rate limit errors`
  - `docs(api): update endpoint specs`

### Testing Strategy
```
tests/
├── unit/
│   ├── test_tokenizer.py
│   ├── test_scraper.py
│   └── test_pipeline.py
├── integration/
│   └── test_end_to_end.py
└── fixtures/
    └── sample_posts.json
```

## References

- [Sheng Dictionary Research](https://www.researchgate.net/publication/)
- [Code-Switching in African NLP](https://arxiv.org/)
- [Nairobi Informal Economy Report 2024](https://)

---

*Architecture version: 0.1.0*
*Last updated: 2026-04-29*
