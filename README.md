# Sheng-Sentiment-Base

**Project Sheng V1**: The foundational NLP infrastructure for Kenya's informal economy.

[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> *"Building the engine, not just the car."*

## Overview

Sheng-Sentiment-Base is a high-fidelity NLP preprocessing engine for **Sheng**—Nairobi's dynamic urban slang that blends Swahili, English, and local dialects. This infrastructure layer enables accurate sentiment analysis, text classification, and language understanding where generic LLMs fail.

### The Problem
Global AI models (GPT-4, Gemini) struggle with:
- **Code-switching patterns**: "Hii mbogi ni fiti" → "This crew is good"
- **Rapidly evolving slang**: New terms emerge weekly in Nairobi's streets
- **Context-dependent sentiment**: "Kudunda" can mean partying (positive) or failing (negative)

### The Solution
A specialized "Cultural API" that:
- Normalizes Sheng variant spellings ('ronga' → 'rongai')
- Detects code-switching boundaries
- Applies contextual sentiment rules
- Provides training-ready datasets for fine-tuning

## Quick Start

```bash
# Clone the repository
git clone https://github.com/okech-christopher/sheng-sentiment-base.git
cd sheng-sentiment-base

# Install dependencies
pip install -r requirements.txt

# Run the tokenizer
python -m src.tokenizers.sheng_tokenizer
```

## Usage

### API Usage (FastAPI Service)

Start the API server:

```bash
# Development mode
python -m src.api.main

# Production mode
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

**Analyze Sheng text via API:**

```bash
curl -X POST http://localhost:8000/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Karao wako mabs, jam imetupa",
    "include_logistics": true,
    "include_code_switches": true
  }'
```

**Response:**

```json
{
  "original_text": "Karao wako mabs, jam imetupa",
  "normalized_text": "karao wako mabs jam imetupa",
  "tokens": ["karao", "wako", "mabs", "jam", "imetupa"],
  "slang_terms": ["karao", "mabs", "jam"],
  "code_switches": [],
  "sentiment_score": -0.5,
  "sentiment_label": "negative",
  "logistics_intent": {
    "intent": "police_report",
    "severity": "medium",
    "description": "Police checkpoint or presence detected"
  },
  "is_logistics": true,
  "confidence": 0.6,
  "metadata": {
    "token_count": 5,
    "slang_count": 3,
    "switch_count": 0,
    "has_logistics_intent": true
  }
}
```

**Run the demo script:**

```bash
# Start the API in a terminal
python -m src.api.main

# In another terminal, run the demo
python demo_api.pyIn Progrss
```

###xTokenize Sheng Text

```python
from src.tokenizers.sheng_tokenizer import ShengTokenizer

tokenizer = ShengTokenizer()

result = tokenizer.tokenize("Buda hana chapaa, amekudunda")
# Output: normalized text, slang terms detected, contextual sentiment

print(f"Sentiment: {result.sentiment_label}")  # negative
print(f"Slang: {result.slang_terms}")  # ['buda', 'chapaa', 'kudunda']
```

### Scrape and Process

```python
from src.pipelines.sheng_pipeline import ShengPipeline

pipeline = ShengPipeline()

# Scrape and process in one step
results = pipeline.scrape_and_process("sheng", count=100)

# Export for LLM training
pipeline.export_to_training_format("training_data.jsonl")
```

## Project Structure

```
sheng_sentiment_base/
├── src/
│   ├── scrapers/          # Data collection (X/TikTok)
│   ├── tokenizers/        # NLP preprocessing
│   ├── pipelines/         # End-to-end workflows
│   └── utils/             # Helpers
├── data/
│   ├── raw/               # Scraped content
│   ├── processed/         # Cleaned datasets
│   └── dictionaries/      # Sheng slang mappings
├── tests/                 # Unit tests
├── docs/                  # Documentation
└── notebooks/             # Exploration
```

## Architecture

See [ARCH.md](ARCH.md) for detailed system design.

## Roadmap

### Phase 1: Foundation (Complete)
- [x] Sheng tokenizer with normalization
- [x] Basic scraper framework
- [x] Contextual sentiment engine
- [x] Dictionary with 75+ slang mappings

### Phase 2: Scale (Next)
- [ ] Collect 10,000+ labeled samples
- [ ] Fine-tune Llama-3/Mistral on Sheng
- [ ] REST API for real-time inference
- [ ] Boda-Pulse GIS integration

### Phase 3: Ecosystem (Future)
- [ ] Chama-Chain credit scoring
- [ ] Trust-Grid escrow protocol
- [ ] Multi-dialect expansion (Lagos, Accra)

## Contributing

This project follows strict coding standards:
- Type hints on all functions
- Google-style docstrings
- Conventional commits (`feat(nlp): add tokenizer`)
- PEP 8 compliance

## The Vision

> "Software is eating the world, but *context* is eating software."

In Kenya, the informal economy represents **83% of employment** and **$1B+ in gig sector value**. By instrumenting this "invisible" knowledge, we create the infrastructure layer for Africa's next 100 million digital users.

**Target Markets:**
- **Contextual AI Data**: $20B (20-year projection)
- **Shadow Logistics**: $12B
- **Social Commerce**: $15B
- **Digital Chamas**: $50B

## Connect

- **Builder**: [@okech-christopher](https://github.com/okech-christopher)
- **Status**: 0.91 Production Hardening (Day 3 of 7300)
- **Location**: Nairobi, Kenya

## Compliance

**Kenya AI Bill 2026 Alignment**:
- **Transparency**: All sentiment and intent decisions are explainable through rule-based logic
- **Bias Mitigation**: RecursiveSlangResolver prevents single-intent bias through weighting matrix
- **Data Privacy**: No personal data collection; all processing is on-premise
- **Accountability**: Full audit trail with confidence scores and reasoning metadata

## License

MIT License - See [LICENSE](LICENSE) for details.

---

*Built with the Nvidia mindset: architect systems that outlast the code.*
