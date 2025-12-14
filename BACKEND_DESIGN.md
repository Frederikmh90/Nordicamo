# NAMO Backend & Database Design

**Version:** Draft 1.0  
**Date:** November 18, 2025

---

## Overview

This document outlines the architecture for the NAMO (Nordic Alternative Media Observatory) backend system, including:
- PostgreSQL database schema
- FastAPI backend structure
- Data analytics endpoints
- Update pipeline for bi-annual data refreshes

---

## 1. Database Schema Design

### 1.1 Core Tables

#### `articles` table (main data table)

```sql
CREATE TABLE articles (
    -- Primary key
    id BIGSERIAL PRIMARY KEY,
    
    -- Original article data
    url TEXT NOT NULL UNIQUE,
    title TEXT,
    description TEXT,
    content TEXT,
    author TEXT,
    published_date TIMESTAMP,
    extraction_method VARCHAR(50),
    domain VARCHAR(255) NOT NULL,
    country VARCHAR(50),
    content_length INTEGER,
    scraped_at TIMESTAMP,
    
    -- Actor/partisan data
    actor_name VARCHAR(255),
    actor_country VARCHAR(50),
    partisan VARCHAR(50),  -- Right, Left, Other
    partisan_full TEXT,
    
    -- NLP enrichment
    sentiment VARCHAR(20),  -- positive, negative, neutral
    sentiment_score FLOAT,
    categories JSONB,  -- Array of categories
    entities JSONB,    -- Structured entity data
    external_links JSONB,  -- Array of URLs
    
    -- Processing metadata
    preprocessed_at TIMESTAMP,
    nlp_processed_at TIMESTAMP,
    
    -- Derived fields for analytics
    word_count INTEGER,
    year INTEGER GENERATED ALWAYS AS (EXTRACT(YEAR FROM published_date)) STORED,
    month INTEGER GENERATED ALWAYS AS (EXTRACT(MONTH FROM published_date)) STORED,
    year_month VARCHAR(7) GENERATED ALWAYS AS (TO_CHAR(published_date, 'YYYY-MM')) STORED,
    
    -- Update tracking
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for common queries
CREATE INDEX idx_articles_domain ON articles(domain);
CREATE INDEX idx_articles_country ON articles(country);
CREATE INDEX idx_articles_partisan ON articles(partisan);
CREATE INDEX idx_articles_published_date ON articles(published_date);
CREATE INDEX idx_articles_year_month ON articles(year_month);
CREATE INDEX idx_articles_sentiment ON articles(sentiment);
CREATE INDEX idx_articles_categories ON articles USING GIN(categories);
CREATE INDEX idx_articles_entities ON articles USING GIN(entities);

-- Full text search index
CREATE INDEX idx_articles_title_search ON articles USING GIN(to_tsvector('english', title));
CREATE INDEX idx_articles_content_search ON articles USING GIN(to_tsvector('english', content));
```

#### `actors` table (reference data)

```sql
CREATE TABLE actors (
    id SERIAL PRIMARY KEY,
    domain VARCHAR(255) NOT NULL UNIQUE,
    actor_name VARCHAR(255) NOT NULL,
    country VARCHAR(50),
    primary_format VARCHAR(100),
    secondary_format VARCHAR(100),
    partisan VARCHAR(50),
    partisan_full TEXT,
    self_description TEXT,
    
    -- Social media links
    website TEXT,
    facebook_page TEXT,
    facebook_group TEXT,
    twitter TEXT,
    instagram TEXT,
    youtube TEXT,
    telegram TEXT,
    vkontakte TEXT,
    tiktok TEXT,
    gab TEXT,
    
    -- Metadata
    notes TEXT,
    about TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_actors_domain ON actors(domain);
CREATE INDEX idx_actors_country ON actors(country);
CREATE INDEX idx_actors_partisan ON actors(partisan);
```

#### `data_updates` table (tracking bi-annual updates)

```sql
CREATE TABLE data_updates (
    id SERIAL PRIMARY KEY,
    update_date DATE NOT NULL,
    data_version VARCHAR(50),  -- e.g., "2025_09"
    articles_added INTEGER,
    articles_updated INTEGER,
    articles_total INTEGER,
    status VARCHAR(50),  -- pending, processing, complete, failed
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    notes TEXT
);
```

### 1.2 Partitioning Strategy (Optional, for performance)

For 9.5M+ articles, consider partitioning by year or country:

```sql
-- Partition by year (recommended)
CREATE TABLE articles (
    -- ... same columns as above ...
) PARTITION BY RANGE (published_date);

CREATE TABLE articles_2020 PARTITION OF articles
    FOR VALUES FROM ('2020-01-01') TO ('2021-01-01');

CREATE TABLE articles_2021 PARTITION OF articles
    FOR VALUES FROM ('2021-01-01') TO ('2022-01-01');

-- ... continue for each year ...
```

---

## 2. FastAPI Backend Structure

### 2.1 Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app initialization
│   ├── config.py               # Configuration & environment variables
│   ├── database.py             # Database connection & session management
│   │
│   ├── models/                 # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── article.py
│   │   └── actor.py
│   │
│   ├── schemas/                # Pydantic models for request/response
│   │   ├── __init__.py
│   │   ├── article.py
│   │   └── analytics.py
│   │
│   ├── api/                    # API endpoints
│   │   ├── __init__.py
│   │   ├── articles.py         # Article CRUD
│   │   ├── analytics.py        # Analytics endpoints
│   │   ├── search.py           # Search functionality
│   │   └── stats.py            # Statistics endpoints
│   │
│   ├── services/               # Business logic
│   │   ├── __init__.py
│   │   ├── article_service.py
│   │   ├── analytics_service.py
│   │   └── cache_service.py
│   │
│   └── utils/
│       ├── __init__.py
│       └── helpers.py
│
├── migrations/                 # Alembic database migrations
├── tests/                      # Test suite
├── requirements.txt
└── .env                        # Environment variables
```

### 2.2 Key API Endpoints

#### Analytics Endpoints (Most Important)

```python
# Basic statistics
GET /api/analytics/overview
    → Returns: total articles, date range, country distribution, partisan distribution

GET /api/analytics/articles-by-country
    → Returns: Article count per country (with optional date filters)

GET /api/analytics/articles-by-partisan
    → Returns: Article count by partisan leaning (Right/Left/Other)

GET /api/analytics/articles-over-time
    Query params: ?country=denmark&partisan=Right&granularity=month
    → Returns: Time series data for charts

GET /api/analytics/sentiment-distribution
    Query params: ?country=&partisan=&date_from=&date_to=
    → Returns: Sentiment distribution (positive/negative/neutral percentages)

GET /api/analytics/top-categories
    Query params: ?country=&partisan=&limit=10
    → Returns: Most common article categories

GET /api/analytics/top-actors
    Query params: ?country=&partisan=&limit=20
    → Returns: Most active outlets by article count

GET /api/analytics/entity-analysis
    Query params: ?entity_type=persons&country=&limit=50
    → Returns: Most mentioned persons/orgs/locations

# Time-based trends
GET /api/analytics/trends/sentiment
    Query params: ?granularity=month&country=&partisan=
    → Returns: Sentiment trends over time

GET /api/analytics/trends/categories
    Query params: ?granularity=month&category=Politics
    → Returns: Category frequency over time
```

#### Article Endpoints

```python
# Basic CRUD
GET /api/articles
    Query params: ?country=&partisan=&sentiment=&date_from=&date_to=&limit=50&offset=0
    → Returns: Paginated list of articles

GET /api/articles/{id}
    → Returns: Single article with all details

# Search
GET /api/search
    Query params: ?q=Trump&country=&partisan=&limit=50
    → Returns: Full-text search results

# Random sample (for exploration)
GET /api/articles/random
    Query params: ?country=&partisan=&limit=10
    → Returns: Random sample of articles
```

#### Actor Endpoints

```python
GET /api/actors
    → Returns: List of all actors/outlets

GET /api/actors/{domain}
    → Returns: Actor details and their article stats

GET /api/actors/{domain}/articles
    Query params: ?limit=50&offset=0
    → Returns: Articles from specific actor
```

### 2.3 Example Response Formats

#### Analytics Overview Response

```json
{
  "total_articles": 9578179,
  "date_range": {
    "earliest": "2015-01-01",
    "latest": "2025-11-15"
  },
  "by_country": {
    "denmark": 2340500,
    "sweden": 3120800,
    "norway": 2018300,
    "finland": 2098579
  },
  "by_partisan": {
    "Right": 6100000,
    "Left": 2200000,
    "Other": 1278179
  },
  "sentiment_distribution": {
    "positive": 15.2,
    "neutral": 62.3,
    "negative": 22.5
  },
  "top_categories": [
    {"category": "Politics & Governance", "count": 3200000, "percentage": 33.4},
    {"category": "Immigration & National Identity", "count": 1800000, "percentage": 18.8}
  ]
}
```

#### Articles Over Time Response

```json
{
  "granularity": "month",
  "filters": {
    "country": "denmark",
    "partisan": "Right"
  },
  "data": [
    {"date": "2023-01", "count": 12400},
    {"date": "2023-02", "count": 13200},
    {"date": "2023-03", "count": 14100}
  ]
}
```

---

## 3. Data Loading Pipeline

### 3.1 Initial Load Script

```python
# scripts/03_load_to_postgres.py

"""
Load enriched data from Parquet into PostgreSQL database.
Handles bulk insertion with progress tracking.
"""

import polars as pl
from sqlalchemy import create_engine
from tqdm import tqdm

def load_to_postgres(
    parquet_path: str,
    db_url: str,
    chunk_size: int = 10000,
    table_name: str = "articles"
):
    """
    Load data from Parquet into PostgreSQL in chunks.
    """
    # Read parquet
    df = pl.read_parquet(parquet_path)
    
    # Create database engine
    engine = create_engine(db_url)
    
    # Convert to pandas for SQL insertion (polars doesn't have native SQL support yet)
    df_pandas = df.to_pandas()
    
    # Load in chunks
    total_rows = len(df_pandas)
    for start_idx in tqdm(range(0, total_rows, chunk_size)):
        end_idx = min(start_idx + chunk_size, total_rows)
        chunk = df_pandas.iloc[start_idx:end_idx]
        
        chunk.to_sql(
            table_name,
            engine,
            if_exists='append',
            index=False,
            method='multi'
        )
```

### 3.2 Update Pipeline (Bi-annual Refresh)

```python
# scripts/04_update_database.py

"""
Update database with new articles from bi-annual data refresh.
- Identifies new articles (by URL)
- Updates existing articles if content changed
- Tracks update statistics
"""

def update_database(
    new_data_path: str,
    db_url: str,
    update_version: str = "2026_03"
):
    """
    Smart update: insert new, update changed, skip duplicates.
    """
    # Read new data
    df_new = pl.read_parquet(new_data_path)
    
    # Query existing URLs from database
    existing_urls = get_existing_urls(db_url)
    
    # Identify new articles
    df_new_articles = df_new.filter(~pl.col('url').is_in(existing_urls))
    
    # Insert new articles
    insert_articles(df_new_articles, db_url)
    
    # Optional: Update existing articles if content changed
    # (requires content hash comparison)
    
    # Log update statistics
    log_update(update_version, len(df_new_articles), db_url)
```

---

## 4. Caching Strategy

For performance, implement caching for common queries:

```python
# Use Redis for caching
from redis import Redis
import json

redis_client = Redis(host='localhost', port=6379, db=0)

def get_cached_or_compute(cache_key: str, compute_func, ttl: int = 3600):
    """
    Check cache first, compute if miss, store result.
    """
    # Check cache
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Compute
    result = compute_func()
    
    # Cache result
    redis_client.setex(cache_key, ttl, json.dumps(result))
    
    return result

# Usage in endpoints
@app.get("/api/analytics/overview")
async def get_overview():
    return get_cached_or_compute(
        "analytics:overview",
        compute_overview_stats,
        ttl=3600  # Cache for 1 hour
    )
```

---

## 5. Dashboard Visualizations (Streamlit)

### 5.1 Simple Visualizations to Start

#### Page 1: Overview Dashboard

```
┌─────────────────────────────────────────────────────────────┐
│  NAMO - Nordic Alternative Media Observatory                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  📊 Key Metrics                                             │
│  ┌──────────┬──────────┬──────────┬──────────┐             │
│  │ 9.5M     │ 75       │ 4        │ 10 Years │             │
│  │ Articles │ Outlets  │ Countries│ Coverage │             │
│  └──────────┴──────────┴──────────┴──────────┘             │
│                                                             │
│  📈 Articles by Country (Bar Chart)                         │
│  ████████████ Sweden (3.1M)                                 │
│  ██████████ Denmark (2.3M)                                  │
│  █████████ Finland (2.1M)                                   │
│  ████████ Norway (2.0M)                                     │
│                                                             │
│  🎯 Partisan Distribution (Pie Chart)                       │
│     Right: 53% | Left: 24% | Other: 23%                    │
│                                                             │
│  📅 Articles Over Time (Line Chart)                         │
│     [Interactive time series with country filter]           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### Page 2: Country-Specific Analysis

```
┌─────────────────────────────────────────────────────────────┐
│  Country: [Denmark ▼]                                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Top Outlets:                                               │
│  1. Outlet A - 450K articles (Right)                        │
│  2. Outlet B - 320K articles (Left)                         │
│  3. Outlet C - 280K articles (Other)                        │
│                                                             │
│  Sentiment Distribution:                                    │
│  Positive: 14% | Neutral: 65% | Negative: 21%              │
│                                                             │
│  Top Categories:                                            │
│  [Bar chart of category distribution]                       │
│                                                             │
│  Publication Trends:                                        │
│  [Line chart showing articles per month]                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### Page 3: Topic Explorer

```
┌─────────────────────────────────────────────────────────────┐
│  Category: [Politics & Governance ▼]                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Distribution by Country:                                   │
│  [Stacked bar chart]                                        │
│                                                             │
│  Sentiment Analysis:                                        │
│  [Sentiment over time line chart]                           │
│                                                             │
│  Top Entities Mentioned:                                    │
│  Persons: Trump (12K), Putin (8K), Merkel (6K)             │
│  Organizations: EU (15K), NATO (10K), UN (7K)              │
│  Locations: Ukraine (20K), Russia (18K), USA (16K)         │
│                                                             │
│  Sample Articles:                                           │
│  [Paginated table with title, outlet, date, sentiment]     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Streamlit Code Structure

```python
# frontend/app.py

import streamlit as st
import requests
import plotly.express as px
import pandas as pd

# Configuration
API_BASE_URL = "http://localhost:8000/api"

st.set_page_config(
    page_title="NAMO - Nordic Alternative Media Observatory",
    page_icon="📰",
    layout="wide"
)

# Sidebar navigation
page = st.sidebar.radio(
    "Navigation",
    ["Overview", "Country Analysis", "Topic Explorer", "Search"]
)

if page == "Overview":
    show_overview_page()
elif page == "Country Analysis":
    show_country_page()
elif page == "Topic Explorer":
    show_topic_page()
elif page == "Search":
    show_search_page()

def show_overview_page():
    st.title("📰 NAMO - Nordic Alternative Media Observatory")
    
    # Fetch data from API
    overview_data = requests.get(f"{API_BASE_URL}/analytics/overview").json()
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Articles", f"{overview_data['total_articles']:,}")
    col2.metric("Outlets", "75")
    col3.metric("Countries", "4")
    col4.metric("Years", "10")
    
    # Country distribution
    st.subheader("Articles by Country")
    country_data = pd.DataFrame(
        overview_data['by_country'].items(),
        columns=['Country', 'Articles']
    )
    fig = px.bar(country_data, x='Country', y='Articles')
    st.plotly_chart(fig, use_container_width=True)
    
    # Time series
    st.subheader("Articles Over Time")
    time_data = requests.get(
        f"{API_BASE_URL}/analytics/articles-over-time?granularity=month"
    ).json()
    # ... plot time series ...
```

---

## 6. Deployment Considerations

### 6.1 Local Development Setup

```bash
# 1. Set up PostgreSQL
brew install postgresql  # macOS
# or
sudo apt install postgresql  # Linux

createdb namo_db

# 2. Set up backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Initialize database
alembic upgrade head

# 4. Load data
python scripts/03_load_to_postgres.py \
  --input data/nlp_enriched/NAMO_full.parquet \
  --db-url postgresql://localhost/namo_db

# 5. Run backend
uvicorn app.main:app --reload --port 8000

# 6. Run frontend (separate terminal)
cd frontend
streamlit run app.py --server.port 8501
```

### 6.2 Production Deployment (Remote Server)

```bash
# On server: ssh frede@212.27.13.34 -p 2111

# 1. Install PostgreSQL
sudo apt update && sudo apt install postgresql postgresql-contrib

# 2. Configure PostgreSQL for production
# - Set max_connections
# - Configure shared_buffers (25% of RAM)
# - Enable logging

# 3. Deploy with Docker (recommended)
docker-compose up -d

# 4. Set up nginx as reverse proxy
# - Backend: proxy to :8000
# - Frontend: proxy to :8501
# - SSL with Let's Encrypt

# 5. Set up systemd services for auto-restart
```

---

## 7. Next Steps & Priorities

### Immediate (Week 1-2)

1. ✅ Complete NLP processing on test set (100 articles)
2. ⏳ Create PostgreSQL schema and test with small dataset
3. ⏳ Build basic FastAPI endpoints (overview, articles-by-country)
4. ⏳ Create simple Streamlit dashboard with 2-3 visualizations

### Short-term (Week 3-4)

1. Process larger sample (10K-100K articles) with NLP pipeline
2. Load into PostgreSQL and benchmark query performance
3. Expand API endpoints (sentiment, categories, entities)
4. Add more dashboard visualizations
5. Implement caching

### Medium-term (Month 2)

1. Process full 9.5M articles on GPU server
2. Optimize database queries and add more indexes
3. Complete all dashboard pages
4. Deploy to production server
5. Set up automated backups

### Long-term (Month 3+)

1. Implement bi-annual update pipeline
2. Add user authentication (if needed)
3. Advanced analytics (topic modeling visualization)
4. Methods paper writing
5. Public launch

---

## Questions for Discussion

1. **Database:** Should we partition the articles table? By date or country?
2. **API Design:** Any specific endpoints or analytics you need?
3. **Dashboard:** What visualizations are most important for your research?
4. **Performance:** What query response times are acceptable? (<1s, <5s?)
5. **Updates:** How should we handle article updates vs new insertions?
6. **Access:** Will the dashboard be public or require authentication?

---

**Next Action:** Discuss this design and get your feedback before implementation!

