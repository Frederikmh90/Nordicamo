# NAMO Backend Design Discussion

**Date:** November 25, 2025  
**Status:** Ready for Discussion

---

## Overview

This document outlines the proposed backend architecture for the NAMO dashboard. We'll start simple and build up complexity as needed.

---

## Architecture Overview

```
┌─────────────────┐
│  Streamlit UI   │  (Frontend Dashboard)
│   (Port 8501)   │
└────────┬────────┘
         │ HTTP Requests
         ▼
┌─────────────────┐
│  FastAPI Backend│  (REST API)
│   (Port 8000)   │
└────────┬────────┘
         │ SQL Queries
         ▼
┌─────────────────┐
│  PostgreSQL DB  │  (Data Storage)
│   (Port 5432)   │
└─────────────────┘
```

**Why this stack?**
- **FastAPI**: Modern, fast Python API framework. Perfect for data analytics APIs. Auto-generates API docs.
- **Streamlit**: Python-based dashboard framework. Great for research dashboards, quick to develop.
- **PostgreSQL**: Robust, handles JSONB well (for categories/entities), excellent for analytics queries.

---

## Phase 1: Simple Descriptive Statistics (START HERE)

### 1.1 Basic Statistics Endpoints

Let's start with the most essential queries:

#### **GET `/api/stats/overview`**
Returns basic counts and distributions.

**Response:**
```json
{
  "total_articles": 953846,
  "total_outlets": 75,
  "date_range": {
    "earliest": "1996-01-21",
    "latest": "2025-09-08"
  },
  "by_country": {
    "denmark": 2340500,
    "sweden": 3120800,
    "norway": 2018300,
    "finland": 2098579
  },
  "by_partisan": {
    "Right": 5100000,
    "Left": 2300000,
    "Other": 2178179
  }
}
```

**SQL Query:**
```sql
SELECT 
  COUNT(*) as total_articles,
  COUNT(DISTINCT domain) as total_outlets,
  MIN(date) as earliest_date,
  MAX(date) as latest_date
FROM articles;

SELECT country, COUNT(*) 
FROM articles 
WHERE country IS NOT NULL 
GROUP BY country;

SELECT partisan, COUNT(*) 
FROM articles 
WHERE partisan IS NOT NULL 
GROUP BY partisan;
```

#### **GET `/api/stats/articles-by-country`**
Article counts per country (with optional filters).

**Query Params:** `?partisan=Right&date_from=2023-01-01&date_to=2024-01-01`

**Response:**
```json
{
  "filters": {
    "partisan": "Right",
    "date_from": "2023-01-01",
    "date_to": "2024-01-01"
  },
  "data": [
    {"country": "denmark", "count": 450000},
    {"country": "sweden", "count": 620000},
    {"country": "norway", "count": 380000},
    {"country": "finland", "count": 410000}
  ]
}
```

#### **GET `/api/stats/articles-over-time`**
Time series data for line charts.

**Query Params:** `?country=denmark&granularity=month&partisan=Right`

**Response:**
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

**SQL Query:**
```sql
SELECT 
  TO_CHAR(date, 'YYYY-MM') as date,
  COUNT(*) as count
FROM articles
WHERE country = 'denmark' 
  AND partisan = 'Right'
  AND date >= '2023-01-01'
GROUP BY TO_CHAR(date, 'YYYY-MM')
ORDER BY date;
```

### 1.2 Simple Dashboard Visualizations

**Page 1: Overview**
- Key metrics cards (total articles, outlets, countries, date range)
- Bar chart: Articles by country
- Pie chart: Partisan distribution
- Line chart: Articles over time (all countries)

**Page 2: Country Analysis**
- Dropdown to select country
- Bar chart: Articles by partisan (for selected country)
- Line chart: Articles over time (for selected country)
- Table: Top 10 outlets by article count

**Page 3: Outlet Analysis**
- Dropdown to select outlet/domain
- Line chart: Publication frequency over time
- Sentiment distribution (if NLP processed)
- Top categories (if NLP processed)

---

## Phase 2: Enhanced Statistics (After Phase 1 Works)

### 2.1 Sentiment Analysis

#### **GET `/api/stats/sentiment-distribution`**
Sentiment breakdown by filters.

**Query Params:** `?country=denmark&partisan=Right`

**Response:**
```json
{
  "filters": {"country": "denmark", "partisan": "Right"},
  "sentiment": {
    "positive": {"count": 680000, "percentage": 15.1},
    "neutral": {"count": 2920000, "percentage": 64.9},
    "negative": {"count": 900000, "percentage": 20.0}
  }
}
```

### 2.2 Category Analysis

#### **GET `/api/stats/top-categories`**
Most common categories.

**Query Params:** `?country=denmark&limit=10`

**Response:**
```json
{
  "filters": {"country": "denmark"},
  "categories": [
    {"category": "Politics & Governance", "count": 1200000, "percentage": 26.7},
    {"category": "Immigration & National Identity", "count": 680000, "percentage": 15.1}
  ]
}
```

**SQL Query:**
```sql
SELECT 
  category,
  COUNT(*) as count,
  ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as percentage
FROM articles,
LATERAL jsonb_array_elements_text(categories) as category
WHERE country = 'denmark'
GROUP BY category
ORDER BY count DESC
LIMIT 10;
```

### 2.3 Entity Analysis

#### **GET `/api/stats/top-entities`**
Most mentioned persons/organizations/locations.

**Query Params:** `?entity_type=persons&country=denmark&limit=20`

**Response:**
```json
{
  "entity_type": "persons",
  "filters": {"country": "denmark"},
  "entities": [
    {"name": "Mette Frederiksen", "count": 45000},
    {"name": "Donald Trump", "count": 32000},
    {"name": "Vladimir Putin", "count": 28000}
  ]
}
```

---

## Phase 3: Advanced Features (Future)

### 3.1 Topic Modeling Integration
- Use BERTopic results from reference script
- Visualize topic clusters
- Show topic evolution over time

### 3.2 Search Functionality
- Full-text search across articles
- Filter by country/partisan/category
- Highlight search terms

### 3.3 Comparative Analysis
- Compare outlets side-by-side
- Compare countries
- Compare time periods

---

## Implementation Plan

### Step 1: Database Setup ✅ (Done)
- [x] Create PostgreSQL schema
- [x] Create loading script
- [ ] Test with small dataset (100-1000 articles)

### Step 2: Basic FastAPI Backend
- [ ] Set up FastAPI project structure
- [ ] Create database connection module
- [ ] Implement 3 basic endpoints:
  - `/api/stats/overview`
  - `/api/stats/articles-by-country`
  - `/api/stats/articles-over-time`
- [ ] Test endpoints with Postman/curl

### Step 3: Simple Streamlit Dashboard
- [ ] Create overview page with 3 visualizations
- [ ] Connect to FastAPI backend
- [ ] Test locally

### Step 4: Expand Gradually
- [ ] Add country analysis page
- [ ] Add outlet analysis page
- [ ] Add sentiment/category endpoints
- [ ] Add more visualizations

---

## Questions for You

1. **Visualization Priority**: Which visualizations are most important for your research?
   - Articles by country over time? Yes, this is important - it should be semi-interactive so if you hover over an object, there should be addition information. Please see if there is something in reference scripts. Otherwise top 10 news outlets per country. 
   - Partisan distribution comparisons? Yes, this would be nice as well
   - Sentiment trends? Not imporatnt to begin with.
   - Category analysis? Yes, we need to get started with Qwen2.5 for the categories you suggested.

2. **Dashboard Audience**: Who will use this?
   - Researchers (more detailed)? Media and communication scholars.
   - General public (simpler)? Maybe university students will use it as test data in classes.
   - Journalists (quick insights)? Yes. But think of what would be interesting for them ass well.

3. **Performance Expectations**: 
   - How fast should queries be? (<1s acceptable?) Yes, that is acceptable.
   - Will you need real-time updates or is cached data OK? cached data is alright.

4. **Filtering Needs**: What filters are essential?
   - Country ✓
   - Partisan ✓
   - Date range ✓
   - Category? (after NLP)
   - Sentiment? (after NLP)
   - Outlet/domain? Yes, outlet

5. **Export Functionality**: Do you need to export data?
   - CSV downloads?
   - PDF reports?
   - API access for others? At some point, it should be possible to make a query on the webpage and some kind of form with name, email and request for data. Now that I think of it - I also need to make the code ready for github upload!

---

## Next Steps

1. **Review this design** - Does it match your needs?
2. **Answer questions above** - Helps prioritize features
3. **Test database setup** - Load small test dataset
4. **Build Phase 1** - Start with simplest endpoints
5. **Iterate** - Add features based on what you need

---

## Quick Start Commands

Once we agree on the design:

```bash
# 1. Create database schema
python scripts/03_create_database_schema.py --create-db

# 2. Load test data
python scripts/04_load_data_to_db.py \
  --articles data/processed/NAMO_preprocessed_test.parquet \
  --actors data/NAMO_actor_251118.xlsx \
  --batch-size 100

# 3. Start FastAPI backend (we'll create this)
cd backend
uvicorn app.main:app --reload --port 8000

# 4. Start Streamlit dashboard (we'll create this)
cd frontend
streamlit run app.py --server.port 8501
```

---

**Ready to proceed?** Let me know your thoughts and we'll start building! 🚀

