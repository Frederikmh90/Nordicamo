# Clear Streamlit Cache

The backend endpoints are working correctly. If you're still seeing 404 errors, it's likely due to Streamlit caching.

## Quick Fix

**Option 1: Restart Streamlit**
1. Stop Streamlit (Ctrl+C)
2. Restart: `streamlit run app.py --server.port 8501`

**Option 2: Clear Cache in UI**
1. Click the "⋮" menu (top right)
2. Select "Clear cache"
3. Refresh the page

**Option 3: Clear Cache Manually**
```bash
# Stop Streamlit
# Then delete cache:
rm -rf ~/.streamlit/cache
# Restart Streamlit
```

## Verify Backend is Working

```bash
# Test categories endpoint
curl http://localhost:8000/api/stats/categories

# Test sentiment endpoint  
curl http://localhost:8000/api/stats/sentiment
```

Both should return JSON data, not 404 errors.

## If Still Not Working

Check that the backend is running:
```bash
ps aux | grep uvicorn
```

If not running, start it:
```bash
cd backend
source ../venv/bin/activate
export PATH="/usr/local/opt/postgresql@14/bin:$PATH"
python -m uvicorn app.main:app --reload --port 8000
```

