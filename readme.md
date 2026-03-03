# Monday.com Business Intelligence Agent 🚀

A FastAPI-based Business Intelligence (BI) Agent that connects to Monday.com using live GraphQL queries and answers founder-level natural language business questions such as pipeline value, sector performance, and quarterly summaries.

---

## 📌 Project Overview

This project implements a lightweight AI-driven BI assistant that:

- Connects to Monday.com via GraphQL API
- Fetches live board data at query time
- Dynamically detects relevant columns (Sector, Revenue, Date)
- Applies business filters (sector, quarter)
- Aggregates results in real time
- Generates executive-level insights
- Returns structured JSON responses
- Displays execution trace logs for transparency

The system simulates a simplified AI-powered analytics assistant designed for founders and executives.

---

## 🏗 Architecture Overview

### Tech Stack

- **FastAPI** – Backend API framework  
- **Monday.com GraphQL API** – Live data source  
- **Python** – Data parsing, normalization, and aggregation  
- **Uvicorn** – ASGI server  
- **python-dotenv** – Secure environment variable management  

---

### Flow

1. User sends a natural language query to `/ask`
2. FastAPI receives the request
3. The system makes live GraphQL API calls to Monday.com
4. Board items and column values are fetched in real time
5. The agent dynamically:
   - Detects sector column
   - Detects revenue/value column
   - Detects date column
   - Applies filters (sector, quarter)
   - Aggregates totals
6. Returns structured response with:
   - Executive summary
   - Sector breakdown
   - Data quality note
   - Trace logs

No caching or preloading is used — all data is fetched live at query time.

---

## 🔄 Live Query-Time Fetching

This application strictly implements live query-time fetching:

- Every API request triggers fresh GraphQL calls
- No data is stored locally
- No caching mechanism is used

This guarantees real-time business accuracy.

---

## 📊 Business Intelligence Capabilities

The agent provides:

- Total pipeline value
- Deal count
- Average deal size
- Pipeline health classification (Strong / Moderate / Weak)
- Sector concentration percentage
- Sector performance breakdown
- Data quality transparency (missing/null handling)

It also asks clarifying questions when queries are ambiguous.

---

## 📊 Example Queries

### 1️⃣ Pipeline Overview
```json
{
  "question": "How is our pipeline looking this quarter?"
}