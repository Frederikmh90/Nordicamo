# Starting the NAMO Backend Server

## Quick Start

### Option 1: Using the startup script (Recommended)

```bash
cd /Users/Codebase/projects/alterpublics/NAMO_nov25
./backend/start_server.sh
```

### Option 2: Manual start

```bash
cd /Users/Codebase/projects/alterpublics/NAMO_nov25

# Activate virtual environment
source venv/bin/activate

# Navigate to backend directory
cd backend

# Install dependencies if needed
pip install -r requirements.txt

# Start the server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Verify Server is Running

Once started, you should see:
- Server running on `http://localhost:8000`
- API docs at `http://localhost:8000/api/docs`
- Health check at `http://localhost:8000/health`

## Troubleshooting

### Port 8000 already in use
If you get an error that port 8000 is already in use:
```bash
# Find and kill the process using port 8000
lsof -ti:8000 | xargs kill -9

# Or use a different port
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

### Database connection errors
Make sure PostgreSQL is running:
```bash
# Check PostgreSQL status (macOS)
brew services list | grep postgresql

# Start PostgreSQL if needed
brew services start postgresql@14
```

### Missing dependencies
```bash
pip install -r backend/requirements.txt
```

## Running in Background

To run the server in the background:
```bash
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > backend/server.log 2>&1 &
```

To stop it:
```bash
lsof -ti:8000 | xargs kill -9
```

