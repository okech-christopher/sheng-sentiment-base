# Sheng-Native API Reference

**Version:** 0.3.0  
**Base URL:** `http://localhost:8000`

## Overview

The Sheng-Native API provides contextual sentiment analysis and logistics intent detection for Kenyan Sheng text. It bridges the gap between formal AI systems and the informal economy by understanding the nuanced code-switching patterns of Nairobi's urban slang.

## Authentication

Currently, the API does not require authentication. For production deployments, implement API key authentication.

## Endpoints

### Health Check

**GET** `/health`

Check the health status of the API service.

**Response:**
```json
{
  "status": "healthy",
  "version": "0.3.0",
  "model": "Sheng-Native Dictionary v0.3"
}
```

### Text Analysis

**POST** `/v1/analyze`

Analyze Sheng text for sentiment, logistics intent, and code-switching patterns.

**Request Body:**
```json
{
  "text": "Karao wako mabs, jam imetupa",
  "include_logistics": true,
  "include_code_switches": true
}
```

**Parameters:**
- `text` (string, required): Sheng text to analyze (1-1000 characters)
- `include_logistics` (boolean, optional): Include logistics intent detection (default: true)
- `include_code_switches` (boolean, optional): Include code-switching analysis (default: true)

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
    "description": "Police checkpoint or presence"
  },
  "metadata": {
    "token_count": 5,
    "slang_count": 3,
    "switch_count": 0,
    "has_logistics_intent": true
  }
}
```

### System Statistics

**GET** `/v1/stats`

Get system statistics and model information.

**Response:**
```json
{
  "slang_terms_count": 109,
  "sentiment_rules_count": 7,
  "logistics_intent_count": 8,
  "dictionary_version": "v0.3",
  "model_status": "loaded"
}
```

## Logistics Intents

The API can detect the following logistics intents:

| Intent | Severity | Description | Example Slang |
|--------|----------|-------------|---------------|
| `police_report` | medium | Police checkpoint or presence | karao, kanjo |
| `traffic_report` | medium | Traffic congestion | jam, gridlock |
| `obstacle_report` | high | Vehicle breakdown or mechanical failure | mreki, breakdown |
| `location_report` | low | Bus station or transport hub | mabs, stage |
| `route_suggestion` | low | Alternative route recommendation | shorcut, shortcut |
| `route_change` | low | Route reversal or change direction | u-turn, turn |
| `unofficial_route` | medium | Unofficial or informal route | panya, backroute |

## Sentiment Labels

- `positive`: Sentiment score > 0.1
- `negative`: Sentiment score < -0.1
- `neutral`: Sentiment score between -0.1 and 0.1

## Contextual Sentiment

The API uses a 3-token look-ahead window to detect context-dependent sentiment:

**Example 1 - Positive Context:**
```
Input: "Kudunda sherehe, mzinga full!"
Sentiment: positive (party context detected)
```

**Example 2 - Negative Context:**
```
Input: "Ame kudunda mtihani ya kwanza"
Sentiment: negative (exam context detected)
```

## Code-Switching Detection

The API identifies code-switching between Sheng, Swahili, and English:

```
Input: "Hii mbogi ni fiti sana"
Code-switches: ["ni:sheng-english", "sana:sheng-swahili"]
```

## Error Responses

**400 Bad Request**
```json
{
  "detail": "Analysis failed: Invalid input text"
}
```

**503 Service Unavailable**
```json
{
  "detail": "Service not initialized"
}
```

**500 Internal Server Error**
```json
{
  "detail": "Analysis failed: [error message]"
}
```

## Running the API

### Development Mode
```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
python -m src.api.main
```

### Production Mode
```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Rate Limiting

Currently, no rate limiting is implemented. For production, implement rate limiting using middleware.

## Examples

### Example 1: Police Report Detection
```bash
curl -X POST http://localhost:8000/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "Karao wako mabs"}'
```

### Example 2: Contextual Sentiment
```bash
curl -X POST http://localhost:8000/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "Kudunda sherehe, mzinga full!"}'
```

### Example 3: Traffic Report
```bash
curl -X POST http://localhost:8000/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "Jam imekali town, tumia shorcut"}'
```

## Integration with Boda-Pulse

This API serves as the NLP layer for the Boda-Pulse logistics system. When boda-boda riders report street conditions, the API:

1. **Detects Intent**: Identifies police reports, traffic, or obstacles
2. **Extracts Severity**: Categorizes urgency (low/medium/high)
3. **Normalizes Text**: Converts slang to standard forms for database storage

**Integration Flow:**
```
Boda Rider Voice Note → ASR → Sheng-Native API → Structured Report → Boda-Pulse GIS
```

## Roadmap

### v0.4 (Planned)
- [ ] Real-time WebSocket support
- [ ] Batch analysis endpoint
- [ ] Custom dictionary upload
- [ ] API key authentication

### v0.5 (Planned)
- [ ] Voice-to-Text integration
- [ ] Swahili language support
- [ ] Multi-dialect support (Lagos, Accra)

## Support

For issues or questions, contact the development team or open an issue on GitHub.
