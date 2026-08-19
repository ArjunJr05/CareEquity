# Docker Commands - Medical OCR System

## Quick Reference

### Initial Setup (First Time Only)
Run this once to build the images with all dependencies:

```bash
cd c:\Users\njana\Music\CTS_project\CareEquity

docker compose down
docker compose build --no-cache ocr-backend ocr-ui
docker compose up -d
```

### Start System (After Initial Build)
No rebuilding needed - images already exist:

```bash
cd c:\Users\njana\Music\CTS_project\CareEquity

docker compose up -d
```

### Check Status
```bash
docker compose ps
```

Expected output:
```
NAME                 COMMAND                  STATUS
careequity-ocr-backend   "uvicorn src.main:..." Up (healthy)
careequity-ocr-ui        "streamlit run mai..." Up
```

### View Logs
```bash
# Backend logs
docker compose logs -f ocr-backend

# Frontend logs
docker compose logs -f ocr-ui

# All logs
docker compose logs -f
```

### Stop System
```bash
docker compose down
```

### Rebuild Only on Code Changes
If you modify files in `ocr/src/` or `ocr/ocr-ui/`:

```bash
docker compose build --no-cache ocr-backend ocr-ui
docker compose up -d
```

## Key Points

✅ **First build**: Takes 2-3 minutes (installing Python packages)
✅ **Subsequent runs**: Takes 5-10 seconds (images cached)
✅ **No need to rebuild** unless you change Python code
✅ **Always use `--no-cache`** if code changes to get fresh build

## Container URLs

- **Backend API**: http://localhost:8000
  - Health: http://localhost:8000/health
  - Info: http://localhost:8000/info
  - Extract: POST http://localhost:8000/extract

- **Frontend UI**: http://localhost:8501

## Troubleshooting

### Containers won't start
```bash
docker compose logs ocr-backend
docker compose logs ocr-ui
```

### Port already in use
```bash
# Kill process on port 8000
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Kill process on port 8501
netstat -ano | findstr :8501
taskkill /PID <PID> /F

# Then restart
docker compose down
docker compose up -d
```

### Force full rebuild
```bash
docker compose down
docker system prune -a
docker compose build --no-cache ocr-backend ocr-ui
docker compose up -d
```

## File Locations

```
CareEquity/
├── docker-compose.yml          ← Main config
├── ocr/
│   ├── Dockerfile              ← Backend image
│   ├── src/                    ← Backend code
│   ├── ocr-ui/
│   │   ├── Dockerfile          ← Frontend image
│   │   └── main.py             ← Streamlit app
│   └── requirements.txt         ← Python dependencies
└── DOCKER_COMMANDS.md           ← This file
```

## Build vs Run

| Command | Purpose | When |
|---------|---------|------|
| `docker compose build --no-cache ocr-backend` | Create image with dependencies | First time or after code change |
| `docker compose up -d` | Start containers from images | Every time you want to run |
| `docker compose down` | Stop and remove containers | Cleanup, before rebuild |
| `docker system prune -a` | Remove all unused images | Free space, full reset |

