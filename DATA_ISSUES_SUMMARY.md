# Data Issues Summary & Fixes

## Issues Found

### 1. Article Count ✅ FIXED
- **Reported**: 9,578,179 articles
- **Actual**: 953,846 articles
- **Status**: Updated in all documentation

### 2. Date Range ✅ FIXED
- **Reported**: Earliest 2015-01-01
- **Actual**: Earliest 1996-01-21, Latest 2025-09-08
- **Status**: Updated in backend design document

### 3. Missing Domains in Actor Dataset ⚠️ NEEDS ATTENTION

**Missing Domains:**
- `nordfront.dk`: 3,465 articles (Denmark)
- `psst-nyt.dk`: 153 articles (Denmark)

**Total Missing**: 3,618 articles (0.4% of dataset)

**Action Required**: Add these domains to `data/NAMO_actor_251118.xlsx` with appropriate partisan classification.

### 4. NULL Domains ⚠️ NEEDS HANDLING

**Issue**: 140,846 articles (14.8%) have NULL domain values.

**Impact**: These articles cannot be matched to actor dataset for partisan classification.

**Possible Causes**:
- Data extraction issues
- Missing URL information
- Scraping errors

**Recommended Solutions**:
1. **Option A**: Extract domain from URL if URL exists but domain is NULL
2. **Option B**: Mark as "Unknown" partisan and still include in dataset
3. **Option C**: Investigate source data and fix extraction

---

## Domain Mapping Fixes Applied ✅

1. **vastaansanomat.com** → **verkkosanomat.com**
   - Fixed in preprocessing script
   - 1,029 articles now correctly matched

---

## Categories Refined ✅

Updated from 10 to **8 categories**:
1. Politics & Governance
2. Immigration & National Identity
3. Health & Medicine
4. Media & Censorship
5. International Relations & Conflict
6. Economy & Labor
7. Crime & Justice
8. Social Issues & Culture

See `CATEGORIES_REFINED.md` for details.

---

## Next Steps

1. **Add missing domains to actor dataset** (nordfront.dk, psst-nyt.dk)
2. **Handle NULL domains** - decide on approach (extract from URL vs mark as Unknown)
3. **Test preprocessing** with full dataset to verify match rate
4. **Proceed with backend development**

---

## Scripts Created

- `scripts/01b_fix_missing_domains.py` - Analyzes missing domains
- Updated `scripts/01_data_preprocessing.py` - Better domain normalization and debugging

