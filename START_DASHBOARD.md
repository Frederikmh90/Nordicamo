# 🚀 Start NAMO Dashboard

## Quick Start

### 1. Start Backend API (if not running)

```bash
cd /Users/Codebase/projects/alterpublics/NAMO_nov25/backend
source ../venv/bin/activate
export PATH="/usr/local/opt/postgresql@14/bin:$PATH"
python -m uvicorn app.main:app --reload --port 8000
```

**Backend will be available at:** http://localhost:8000
**API Docs:** http://localhost:8000/api/docs

### 2. Start Streamlit Dashboard

**In a new terminal:**

```bash
cd /Users/Codebase/projects/alterpublics/NAMO_nov25/frontend
source ../venv/bin/activate
streamlit run app.py --server.port 8501
```

**Dashboard will be available at:** http://localhost:8501

---

## Features

### 📊 Overview Page
- **Key Metrics**: Total articles, outlets, countries, date range
- **Articles by Country**: Interactive bar chart with hover details
- **Partisan Distribution**: Pie chart showing Right/Left/Other split
- **Articles Over Time**: Multi-country comparison line chart (interactive!)
- **News Categories**: Bar chart showing category distribution
- **Sentiment Analysis**: Sentiment distribution with average scores

### 🌍 Country Analysis Page
- **Top 10 Outlets**: Horizontal bar chart by country
- **Articles Over Time**: Time series with partisan filtering
- **Category Distribution**: Pie chart for selected country
- **Sentiment Analysis**: Country-specific sentiment breakdown

---

## Interactive Features

✅ **Hover Information**: All charts show detailed info on hover
✅ **Multi-country Comparison**: Compare all countries on one chart
✅ **Filtering**: Filter by country, partisan, date range
✅ **Time Granularity**: View by year, month, or week
✅ **Real-time Updates**: Data refreshes every hour (cached)

---

## API Endpoints Used

- `GET /api/stats/overview` - Overview statistics
- `GET /api/stats/articles-by-country` - Articles by country
- `GET /api/stats/articles-over-time` - Time series data
- `GET /api/stats/top-outlets` - Top outlets
- `GET /api/stats/categories` - Category distribution
- `GET /api/stats/sentiment` - Sentiment analysis

---

## Troubleshooting

**Backend not responding:**
- Check PostgreSQL is running: `pg_isready`
- Check backend logs: `/tmp/backend.log`
- Verify database connection in `.env`

**Dashboard not loading:**
- Check backend is running: `curl http://localhost:8000/health`
- Check API URL in `frontend/app.py`: `API_BASE_URL = "http://localhost:8000"`

**No data showing:**
- Verify data is loaded: `psql -U namo_user -d namo_db -c "SELECT COUNT(*) FROM articles;"`
- Check API responses: `curl http://localhost:8000/api/stats/overview`

---

## Next Steps

1. ✅ Backend running
2. ✅ Dashboard ready
3. 🎯 **Start dashboard and explore visualizations!**

```bash
cd frontend && streamlit run app.py
```

Enjoy exploring your Nordic Alternative Media Observatory! 📰

