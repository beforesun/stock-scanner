# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a full-stack A-share (Chinese stock market) quantitative trading screening system with:
- **Backend**: FastAPI + Python 3.11+ with async support
- **Frontend**: Vue 3.3+ with Composition API and Element Plus
- **Database**: PostgreSQL 15 with Redis caching
- **Deployment**: Docker containerized architecture

## Common Development Commands

### Backend Development
```bash
# Start all services
docker-compose up -d

# Access backend container
docker-compose exec backend bash

# Initialize stock data (required on first run)
python scripts/init_stock_list.py

# Download historical data (optional)
python scripts/download_historical_data.py

# Run backend tests (when implemented)
pytest

# Check backend logs
docker-compose logs -f backend
```

### Frontend Development
```bash
# Enter frontend container
docker-compose exec frontend sh

# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Run linter
npm run lint

# Format code
npm run format
```

### Database Operations
```bash
# Access PostgreSQL
docker-compose exec postgres psql -U stock_user -d stock_db

# Access Redis
docker-compose exec redis redis-cli
```

### Manual API Triggers
```bash
# Trigger weekend scan
curl -X POST http://localhost:8000/api/v1/weekend-scan/trigger

# Trigger daily pool scan
curl -X POST http://localhost:8000/api/v1/daily-pool/trigger
```

## High-Level Architecture

### Trading Strategy Pipeline
The system implements a three-stage screening strategy:

1. **Weekend Scan** (`WeekendScanner` service):
   - Filters stocks with closing price > 233-week MA
   - Requires weekly volume > 20-week MA
   - Results stored in `weekend_scan_results` table

2. **Daily Pool** (`DailyScanner` service):
   - Processes weekend scan results
   - Finds volume golden cross (MA20 > MA60)
   - Checks 120-min MACD histogram expansion
   - Results stored in `daily_pool` table

3. **Pattern Recognition** (`PatternRecognizer` service):
   - Identifies "flag consolidation + volume breakout" patterns
   - Finds recent limit-up days with volume contraction during pullback
   - Generates buy signals with stop-loss levels
   - Signals stored in `trade_signals` table

### Service Layer Architecture

The backend follows a layered architecture:

```
API Routes (FastAPI routers)
    ↓
Service Layer (Business logic)
    ├── WeekendScanner - Full market screening
    ├── DailyScanner - Daily filtering
    ├── PatternRecognizer - Pattern identification
    ├── SignalGenerator - Orchestrates pipeline
    └── DataFetcher - External data integration
    ↓
Data Layer (SQLAlchemy models)
    ├── Stock master data
    ├── K-line data (daily/weekly/120min)
    └── Scan results and signals
```

### Key Design Patterns

1. **Async Processing**: All I/O operations use async/await with proper concurrency control via semaphores

2. **Caching Strategy**: Multi-level caching with Redis for scan results and frequently accessed data

3. **Scheduler Integration**: APScheduler manages automated scans at market-specific times:
   - Weekend scan: Sundays 20:00
   - Daily scan: Weekdays 15:05 (after market close)
   - MACD updates: Multiple times during trading hours

4. **Database Design**:
   - Time-series data (K-lines) with proper indexing on (code, date)
   - Soft delete via status fields
   - Foreign key relationships maintain referential integrity

5. **Error Handling**:
   - Comprehensive logging with context
   - Retry mechanisms for external API calls
   - Graceful degradation on failures

### Frontend Architecture

Vue 3 application with:
- **State Management**: Pinia stores for global state
- **API Integration**: Axios client with interceptors
- **UI Components**: Element Plus for consistent design
- **Charts**: ECharts for data visualization
- **Routing**: Vue Router for navigation

### Deployment Notes

- Development uses hot-reload with volume mounts
- Production deployment includes Nginx reverse proxy, SSL, and monitoring (Prometheus/Grafana)
- All services are containerized with proper health checks
- Database migrations run automatically on startup