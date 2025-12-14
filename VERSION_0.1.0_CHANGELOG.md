# Version 0.1.0 - Changelog

**Release Date:** December 2024  
**Status:** ✅ Released

---

## 🎉 What's New in v0.1.0

### ✅ Version Control System
- Git repository initialized
- Semantic versioning implemented (v0.1.0, v0.2.0, etc.)
- Version tags for easy rollback
- Version documentation created (`VERSION_CONTROL.md`)

### ✅ Data Quality Improvements
- **Data quality constants added** to `backend/app/config.py`:
  - `MIN_ARTICLE_DATE = "2003-01-01"` - Uses clean data from 2003+
  - `MAX_FUTURE_DAYS = 90` - Prevents scraper errors with future dates
- All queries already use `clean_articles` view (excludes flagged data)
- Ensures only validated, high-quality data is displayed

### ✅ Enhanced Metrics Dashboard

#### New Key Metrics Displayed:
1. **Data Freshness Indicator**
   - Shows "Updated X hours/days/weeks ago"
   - Displays last article date
   - Auto-updates every minute

2. **Articles per Outlet Average**
   - Shows average number of articles per outlet
   - Helps understand outlet activity levels

3. **Coverage Years**
   - Displays date range (e.g., "2003-2025")
   - Shows temporal span of dataset

4. **Growth Rate**
   - Calculates articles per year trend
   - Shows if article volume is increasing/decreasing over time

### ✅ Outlet Concentration Analysis
- **Market Concentration Metrics**
  - Shows top 3 outlets' percentage of total articles per country
  - Helps identify media concentration
  - Available for all Nordic countries

- **New API Endpoint:** `/api/stats/outlet-concentration`
  - Can filter by country
  - Returns concentration percentage and top outlets details

### ✅ Comparative Analytics
- **Cross-country comparison metrics**
  - Outlet concentration by country
  - Partisan balance ratios
  - Top outlets per country

- **New API Endpoint:** `/api/stats/comparative`
  - Returns comprehensive metrics for all countries
  - Enables side-by-side comparisons

### ✅ Enhanced Overview Endpoint
- **New API Endpoint:** `/api/stats/overview/enhanced`
  - Includes all basic overview metrics
  - Plus: articles per outlet, growth rate, coverage years
  - Backward compatible with basic overview

### ✅ Data Freshness Endpoint
- **New API Endpoint:** `/api/stats/data-freshness`
  - Returns last article date
  - Returns last database update timestamp
  - Calculates hours since last update

---

## 📊 Dashboard Improvements

### Overview Page Updates:
- **5-column KPI strip** (was 4):
  1. Total Articles
  2. Outlets
  3. **Avg per Outlet** (NEW)
  4. Coverage (enhanced with years)
  5. **Growth Rate** (NEW) or Countries

- **Data Freshness Banner** (NEW)
  - Shows at top of overview page
  - Updates automatically

- **Market Concentration Section** (NEW)
  - Shows concentration % for each Nordic country
  - Quick visual comparison

### Visual Enhancements:
- Version badge in header (v0.1.0)
- Better metric formatting with subtitles
- Improved tooltips and help text

---

## 🔧 Technical Changes

### Backend (`backend/app/`)

#### `config.py`
- Added `MIN_ARTICLE_DATE = "2003-01-01"`
- Added `MAX_FUTURE_DAYS = 90`
- Updated `API_VERSION = "0.1.0"`

#### `services/stats_service.py`
- Added `get_data_freshness()` method
- Added `get_enhanced_overview()` method
- Added `get_outlet_concentration()` method
- Added `get_comparative_metrics()` method

#### `api/stats.py`
- Added `/api/stats/overview/enhanced` endpoint
- Added `/api/stats/data-freshness` endpoint
- Added `/api/stats/outlet-concentration` endpoint
- Added `/api/stats/comparative` endpoint

### Frontend (`frontend/app.py`)

#### New Fetch Functions:
- `fetch_enhanced_overview()`
- `fetch_data_freshness()`
- `fetch_outlet_concentration()`
- `fetch_comparative_metrics()`

#### Updated Functions:
- `show_overview_page()` - Enhanced with new metrics
- Added version display in header
- Added data freshness banner
- Added market concentration section

#### Configuration:
- Added `DASHBOARD_VERSION = "0.1.0"`

---

## 📝 Documentation

### New Files:
- `VERSION_CONTROL.md` - Complete guide to version management
- `VERSION_0.1.0_CHANGELOG.md` - This file

### Updated Files:
- `backend/app/config.py` - Added data quality constants
- `frontend/app.py` - Added version and enhanced metrics

---

## 🚀 How to Use Version Control

### View Current Version:
```bash
git describe --tags
# Output: v0.1.0
```

### Switch to v0.1.0:
```bash
git checkout v0.1.0
```

### Create New Version (v0.2.0):
```bash
# 1. Create development branch
git checkout -b v0.2.0-dev

# 2. Update version numbers:
# - backend/app/config.py: API_VERSION = "0.2.0"
# - frontend/app.py: DASHBOARD_VERSION = "0.2.0"

# 3. Make your changes...

# 4. Commit and tag
git add .
git commit -m "Version 0.2.0: [your changes]"
git tag -a v0.2.0 -m "Version 0.2.0 - [description]"
```

See `VERSION_CONTROL.md` for complete guide.

---

## 🐛 Known Issues

None at this time.

---

## 🔮 Future Enhancements (Planned for v0.2.0+)

- [ ] Category diversity score (Shannon index)
- [ ] Entity mention velocity (month-over-month growth)
- [ ] Advanced trend detection (spike alerts)
- [ ] Export functionality (CSV/PDF)
- [ ] Research Hub page
- [ ] Real-time monitoring dashboard
- [ ] Data quality transparency page

---

## 📊 API Endpoints Summary

### New Endpoints:
- `GET /api/stats/overview/enhanced` - Enhanced overview with new metrics
- `GET /api/stats/data-freshness` - Data freshness information
- `GET /api/stats/outlet-concentration?country={country}` - Outlet concentration
- `GET /api/stats/comparative` - Comparative metrics across countries

### Existing Endpoints (unchanged):
- `GET /api/stats/overview` - Basic overview
- `GET /api/stats/articles-by-country`
- `GET /api/stats/articles-over-time`
- `GET /api/stats/top-outlets`
- `GET /api/stats/categories`
- `GET /api/stats/sentiment`
- `GET /api/stats/entities/top`
- `GET /api/stats/entities/statistics`

---

## ✅ Testing Checklist

- [x] Git repository initialized
- [x] Version 0.1.0 tagged
- [x] Data quality constants added
- [x] Enhanced metrics implemented
- [x] Outlet concentration working
- [x] Data freshness displaying
- [x] Dashboard showing all new metrics
- [x] API endpoints tested
- [x] Version documentation created

---

## 🎯 Summary

Version 0.1.0 establishes a solid foundation with:
- ✅ Version control system
- ✅ Data quality filtering
- ✅ Enhanced analytics metrics
- ✅ Comparative analysis tools
- ✅ Professional dashboard presentation

**Ready for production use and future enhancements!**

---

**Next Steps:** Start working on v0.2.0 features or use v0.1.0 as your stable baseline.
