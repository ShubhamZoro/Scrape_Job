# 🤖 Job Scraper

A FastAPI-powered job scraping application that scrapes job listings from **Naukri** and **Foundit**, then ranks them using AI-powered matching based on your resume.

## ✨ Features

- 🔍 **Multi-source Scraping**: Scrape jobs from Naukri and Foundit simultaneously
- 🤖 **AI-Powered Ranking**: Uses OpenAI's GPT-4 to match jobs against your resume
- 📊 **Smart Scoring Algorithm**:
  - **Semantic Match (30%)**: Vector similarity between profile and job description
  - **Skill Match (30%)**: Percentage of required skills match
  - **Experience Match (20%)**: Years of experience alignment
  - **Location Match (10%)**: Location preference alignment
- 📁 **Excel Export**: Download ranked jobs as Excel files
- 🐳 **Docker Support**: Easy deployment with Docker
- 🚀 **AWS EC2**: Fast API Deployed on AWS using EC2

## 🛠️ Tech Stack

- **FastAPI**: Modern, fast web framework for building APIs
- **Selenium**: Web scraping with Chrome driver
- **OpenAI API**: AI-powered job matching and scoring
- **Pandas**: Data manipulation and Excel export
- **Docker**: Containerization for easy deployment

## 📋 Prerequisites

- Python 3.11+
- Chrome browser (for local development)
- OpenAI API key (for AI scoring)

## 🚀 Installation

### Local Development

1. Clone the repository:
```bash
https://github.com/ShubhamZoro/Scrape_Job.git
cd Scrape_Job
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file:
```bash
OPENAI_API_KEY=your_openai_api_key_here
```

5. Run the application:
```bash
uvicorn main:app --reload
```

### Docker Deployment

1. Build the Docker image:
```bash
docker build -t job-scraper .
```

2. Run the container:
```bash
docker run -p 8000:8000 -e OPENAI_API_KEY=your_key_here job-scraper
```

## 📡 API Endpoints

### Health Check
- `GET /health` - Check API health status
- `GET /` - API information and available endpoints

### Job Scraping
- `POST /scrape` - Start job scraping process
  - `job_profiles` (required): Comma-separated job titles (e.g., "Data Scientist,ML Engineer")
  - `experience` (optional): Experience level (e.g., "2-5" or "3")
  - `num_jobs` (optional): Number of jobs per profile (default: 10)
  - `location` (optional): Job location (default: "India")
  - `resume_file` (optional): Resume file (.pdf or .txt) for AI matching

### Task Management
- `GET /status/{task_id}` - Check scraping task status
- `GET /results/{task_id}` - Get scraped jobs as JSON
- `GET /download/{filename}` - Download results Excel file
- `DELETE /cleanup/{task_id}` - Clean up task data and files

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

### Check Status

```bash
curl "http://localhost:8000/status/20240219_120000"
```

### Get Results

```bash
curl "http://localhost:8000/results/20240219_120000"
```

### Download Excel

```bash
curl "http://localhost:8000/download/20240219_120000_ranked_jobs.xlsx" \
  --output ranked_jobs.xlsx
```

## 🚀 Deployment

### Vercel

This project is pre-configured for Vercel deployment with `vercel.json`:

```bash
vercel
```

### Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key for AI job matching

## 📁 Project Structure

```
Scrape_Job/
├── main.py                 # FastAPI application entry point
├── scraper/
│   ├── job_scraper.py     # Main orchestrator
│   ├── ai_scorer.py       # AI-powered job scoring
│   ├── models.py          # Pydantic models
│   ├── utils.py           # Utility functions
│   └── scrapers/
│       ├── naukri_scraper.py    # Naukri.com scraper
│       └── foundit_scraper.py   # Foundit.in scraper
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker configuration
├── vercel.json           # Vercel deployment config
├── uploads/              # Resume upload directory
├── outputs/              # Excel output directory
└── .env                  # Environment variables
```

## ⚠️ Notes

- The scraper uses Selenium with Chrome in headless mode
- Rate limiting is implemented to avoid being blocked
- AI scoring requires a valid OpenAI API key
- Resume files are deleted after processing for privacy

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License.

---

Made with ❤️ for job seekers everywhere
