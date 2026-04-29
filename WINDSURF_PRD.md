# Project Sheng V1: Operational PRD

## Status: April 29, 2026 - Day 1
**Location:** Nairobi, Kenya  
**Mission:** Zero-to-One execution of the "Informal Economy Stack"

---

## Phase 1: The "Sheng-Native" Foundation

### I. Objective
Build a high-fidelity NLP preprocessing engine that cleans and tokenizes Sheng/Swahili-English code-switching data. This engine serves as the "Cultural API" for the broader informal economy stack.

### II. Technical Requirements

#### Data Scraper
- Rate-limited scraper for X (Twitter) and TikTok
- Target: Nairobi geolocation tags and Sheng hashtags (#Sheng, #Nairobian, #MbogiGenje)
- Output: JSONL format with metadata (timestamp, location, engagement)

#### Preprocessing Pipeline
- **Text Normalization:** Handle variations ('ronga'/'rongai', 'dem'/'dame')
- **Contextual Labeling:** Tag sentiment for Kenyan slang (e.g., "Kudunda")
- **Code-Switching Detection:** Identify Swahili/English/Sheng boundaries

#### Deliverables
1. `ShengScraper` class with configurable rate limiting
2. `ShengTokenizer` with slang dictionary integration
3. `ShengPipeline` for end-to-end processing
4. Initial dataset: 10,000 samples by end of Week 1

### III. Today's 12-Hour Sprint (April 29, 2026)

| Time | Task | Deliverable |
|------|------|-------------|
| 0-2h | Repository setup | Git init, `.windsurfrules`, folder structure |
| 2-6h | Scraper module | `ShengScraper` with X/TikTok support |
| 6-10h | Tokenizer | `ShengTokenizer` with normalization |
| 10-12h | Documentation | `README.md`, `ARCH.md` |

---

## Ecosystem Intelligence

### Critical Events (April/May 2026)
- **Connected Africa Summit 2026:** April 27-30, The Edge Convention Centre
- **AI Everything Kenya x GITEX:** May 19-21, KICC
- **Nairobi Startup Summit:** May 28-29, USIU

### Target Contacts
- Investors at AI Everything Kenya Deal Rooms
- Tier 1 Banks (KCB, Equity) for Chama-Chain partnerships
- FMCGs (Unilever, Coca-Cola) for Boda-Pulse data buyers

---

## Success Metrics (Week 1)
- [ ] 10,000 raw samples collected
- [ ] 5 new slang terms identified and mapped
- [ ] Tokenizer achieving >90% accuracy on sentiment classification vs GPT-4 baseline
- [ ] GitHub repo with professional documentation
