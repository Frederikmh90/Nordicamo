# NAMO Backend & Frontend Setup Guide

## Quick Start

### 1. Set Up Backend (FastAPI)

```bash
# Navigate to backend directory
cd backend

# Create virtual environment (if using uv)
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp ../.env.example .env
# Edit .env with your database credentials

# Run the backend server
uvicorn app.main:app --reload --port 8000
```

The API will be available at:
- API: http://localhost:8000
- API Docs: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

### 2. Set Up Frontend (Streamlit)

```bash
# Navigate to frontend directory (in a new terminal)
cd frontend

# Install dependencies
pip install -r requirements.txt

# Run Streamlit app
streamlit run app.py --server.port 8501
```

The dashboard will be available at: http://localhost:8501

## API Endpoints

### Overview Statistics
- `GET /api/stats/overview` - Get overview statistics

### Articles by Country
- `GET /api/stats/articles-by-country?partisan=Right&date_from=2023-01-01` - Get article counts by country

### Articles Over Time
- `GET /api/stats/articles-over-time?country=denmark&granularity=month` - Get time series data

### Top Outlets
- `GET /api/stats/top-outlets?country=denmark&limit=10` - Get top outlets by article count

## Testing the API

```bash
# Test overview endpoint
curl http://localhost:8000/api/stats/overview

# Test articles by country
curl "http://localhost:8000/api/stats/articles-by-country?partisan=Right"

# Test articles over time
curl "http://localhost:8000/api/stats/articles-over-time?country=denmark&granularity=month"
```

## Environment Variables

Create a `.env` file in the `backend` directory:

```env
DB_HOST=localhost
DB_PORT=5432
DB_USER=namo_user
DB_PASSWORD=namo_password
DB_NAME=namo_db
```

## Troubleshooting

1. **Database Connection Error**: Make sure PostgreSQL is running and credentials are correct
2. **API Not Responding**: Check that uvicorn is running on port 8000
3. **Frontend Can't Connect**: Verify API_BASE_URL in Streamlit app matches backend URL

