# 🤖 Job Scraper

A **FastAPI-powered** asynchronous job scraping application that scrapes job listings from **Naukri** and **Foundit**, then ranks them using AI-powered resume matching via OpenAI.

## ✨ Features

- 🔍 **Multi-source Scraping**: Scrapes Naukri and Foundit in parallel across multiple job profiles
- 🤖 **AI-Powered Ranking**: Uses OpenAI `gpt-4o-mini` to match jobs against your resume
- 📊 **Smart Scoring**: Each job is scored with:
  - **Match %**: Overall fit percentage (0–100)
  - **Matching Skills**: Skills you already have
  - **Missing Skills**: Skills to acquire
  - **Match Reason**: 2–3 sentence explanation from AI
- ⚡ **Async + Threaded**: Non-blocking FastAPI with `ThreadPoolExecutor` for heavy scraping
- 📄 **Paginated JSON Results**: Fetch results page by page via REST API
- 🐳 **Docker Support**: Easy containerised deployment

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Web Framework | FastAPI + Uvicorn |
| Scraping | Selenium, BeautifulSoup4, Scrapling, Webdriver-Manager |
| AI Scoring | OpenAI API (`gpt-4o-mini`) |
| PDF Parsing | PyPDF2 |
| Data | Pandas, Pydantic v2 |
| Async | nest-asyncio, asyncio, ThreadPoolExecutor |
| Config | python-dotenv |

## 📋 Prerequisites

- Python 3.11+
- Chrome browser (for Selenium-based scraping)
- OpenAI API key (required for AI scoring)

## 🚀 Installation

### Local Development

1. **Clone the repository:**
```bash
git clone https://github.com/ShubhamZoro/Scrape_Job.git
cd Scrape_Job
```

2. **Create a virtual environment:**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Create a `.env` file:**
```env
OPENAI_API_KEY=your_openai_api_key_here
```

5. **Run the application:**
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`.

### Docker Deployment

1. **Build the image:**
```bash
docker build -t job-scraper .
```

2. **Run the container:**
```bash
docker run -p 8000:8000 -e OPENAI_API_KEY=your_key_here job-scraper
```

## 📡 API Endpoints

### Health & Info

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | API info and available endpoints |
| `GET` | `/health` | Health check with active task count |

### Job Scraping

#### `POST /scrape`
Start an async scraping job. Returns a `task_id` immediately.

| Field | Type | Required | Description |
|---|---|---|---|
| `job_profiles` | `string` | ✅ | Comma-separated job titles, e.g. `"Data Scientist,ML Engineer"` |
| `experience` | `string` | ❌ | Experience range, e.g. `"2-5"` or `"3"` |
| `num_jobs` | `int` | ❌ | Jobs per profile per source (default: `10`, max: `50`) |
| `location` | `string` | ❌ | Job location (default: `"India"`) |
| `resume_file` | `file` | ❌ | Resume (`.pdf` or `.txt`) for AI matching — deleted after processing |

### Task Management

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/status/{task_id}` | Poll task status (`processing` / `completed` / `failed`) |
| `GET` | `/results/{task_id}` | Paginated JSON results (query params: `page`, `page_size`) |
| `DELETE` | `/cleanup/{task_id}` | Remove a completed/failed task from memory |

## 📝 Usage Examples

### Start Scraping

```bash
curl -X POST "http://localhost:8000/scrape" \
  -F "job_profiles=Data Scientist,ML Engineer" \
  -F "experience=2-5" \
  -F "num_jobs=20" \
  -F "location=Bangalore" \
  -F "resume_file=@/path/to/resume.pdf"
```

**Response:**
```json
{
  "task_id": "20240219_120000_123456",
  "status": "processing",
  "message": "Scraping started for 2 profile(s)",
  "profiles": ["Data Scientist", "ML Engineer"]
}
```

### Poll Status

```bash
curl "http://localhost:8000/status/20240219_120000_123456"
```

### Fetch Paginated Results

```bash
curl "http://localhost:8000/results/20240219_120000_123456?page=1&page_size=20"
```

**Response:**
```json
{
  "task_id": "20240219_120000_123456",
  "total_jobs": 42,
  "page": 1,
  "page_size": 20,
  "total_pages": 3,
  "profiles": ["Data Scientist", "ML Engineer"],
  "jobs": [
    {
      "Source": "Naukri",
      "Job Title": "Senior Data Scientist",
      "Skills": "Python, ML, SQL",
      "Match %": 87,
      "Matching Skills": "Python, ML",
      "Missing Skills": "Spark",
      "Match Reason": "Strong alignment in core ML skills..."
    }
  ]
}
```

### Cleanup

```bash
curl -X DELETE "http://localhost:8000/cleanup/20240219_120000_123456"
```

## 📁 Project Structure

```
Scrape_Job/
├── main.py                      # FastAPI app — routes, task lifecycle, thread pool
├── scraper/
│   ├── __init__.py
│   ├── job_scraper.py           # Orchestrator: parallel scraping + AI scoring
│   ├── ai_scorer.py             # OpenAI gpt-4o-mini scoring logic
│   ├── models.py                # Pydantic models (JobSearchResponse, JobResult)
│   ├── utils.py                 # Resume reader (PDF / TXT)
│   └── scrapers/
│       ├── __init__.py
│       ├── naukri_scraper.py    # Naukri.com scraper
│       └── foundit_scraper.py   # Foundit.in scraper
├── simple.py                    # Standalone quick-run script
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Docker configuration
├── uploads/                     # Temporary resume storage (auto-deleted post-scrape)
└── .env                         # Environment variables (not committed)
```

## ⚙️ How It Works

```
POST /scrape
    │
    ├─► Register task_id in memory
    ├─► Save resume temporarily to /uploads
    └─► Dispatch to BackgroundTask
            │
            └─► ThreadPoolExecutor
                    │
                    ├─► NaukriScraper  ─┐
                    └─► FounditScraper ─┴─► Merge all jobs
                                                │
                                                └─► AIScorer (if resume provided)
                                                        │
                                                        └─► Sort by Match %
                                                                │
                                                                └─► Store in task_status
```

## ⚠️ Notes

- Scraping runs in a `ThreadPoolExecutor` (up to 4 workers) — never blocks the event loop
- All profiles × sources are scraped **in parallel** (e.g. 2 profiles × 2 sources = 4 threads)
- Task state is stored **in-memory** — lost on server restart (use Redis for production persistence)
- Uploaded resume files are **automatically deleted** after scraping for privacy
- AI scoring requires a valid `OPENAI_API_KEY`; without it, all jobs return `Match % = 0`
- `task_id` format: `YYYYMMDD_HHMMSS_microseconds` (collision-safe)

## 🤝 Contributing

Contributions are welcome! Feel free to open an issue or submit a Pull Request.

## 📄 License

This project is licensed under the MIT License.

---

Made with ❤️ for job seekers everywhere
