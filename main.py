
import os
import asyncio
import shutil
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import nest_asyncio
from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile

from scraper.job_scraper import JobScraper
from scraper.models import JobSearchResponse

load_dotenv()

# Allow sync Playwright calls inside threads that share the asyncio loop
nest_asyncio.apply()

app = FastAPI(
    title="Job Scraper API",
    description="Scrape and rank job listings from Naukri and Foundit",
    version="1.0.0",
)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Thread pool — scraping is blocking I/O, must not run on the event loop
executor = ThreadPoolExecutor(max_workers=4)

# In-memory task store (swap for Redis in production)
task_status: dict = {}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _run_scraping_sync(
    task_id: str,
    job_profiles: List[str],
    experience: Optional[str],
    num_jobs: int,
    location: str,
    resume_path: Optional[str],
    openai_api_key: Optional[str],
):
    """
    Blocking scraping function.
    Always runs inside ThreadPoolExecutor — never called directly from async code.
    """
    try:
        scraper = JobScraper(
            job_profiles=job_profiles,
            experience=experience,
            num_jobs=num_jobs,
            location=location,
            resume_path=resume_path,
            openai_api_key=openai_api_key,
        )

        jobs_data = scraper.scrape_and_rank()

        if jobs_data:
            task_status[task_id].update({
                "status": "completed",
                "completed_at": datetime.now().isoformat(),
                "total_jobs": len(jobs_data),
                "jobs_data": jobs_data,
            })
        else:
            task_status[task_id].update({
                "status": "failed",
                "completed_at": datetime.now().isoformat(),
                "error": "Scraping finished but no jobs were found",
            })

    except Exception as e:
        task_status[task_id].update({
            "status": "failed",
            "completed_at": datetime.now().isoformat(),
            "error": str(e),
        })

    finally:
        # Always delete the uploaded resume — no physical data retention
        if resume_path and os.path.exists(resume_path):
            os.remove(resume_path)


async def _dispatch_scraping(task_id: str, **kwargs):
    """Hand off blocking work to the thread pool without blocking the event loop."""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        executor,
        lambda: _run_scraping_sync(task_id, **kwargs)
    )


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "message": "Job Scraper API",
        "version": "1.0.0",
        "endpoints": {
            "POST   /scrape": "Start a scraping job",
            "GET    /status/{task_id}": "Poll task status",
            "GET    /results/{task_id}": "Fetch paginated JSON results",
            "DELETE /cleanup/{task_id}": "Remove task from memory",
            "GET    /health": "Health check",
        },
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_tasks": sum(
            1 for t in task_status.values() if t["status"] == "processing"
        ),
        "total_tasks": len(task_status),
    }


@app.post("/scrape", response_model=JobSearchResponse)
async def scrape_jobs(
    background_tasks: BackgroundTasks,
    job_profiles: str = Form(
        ..., description="Comma-separated job profiles e.g. 'Data Scientist, ML Engineer'"
    ),
    experience: Optional[str] = Form(
        None, description="Experience range e.g. '3-5'"
    ),
    num_jobs: int = Form(
        10, description="Jobs per profile per source", ge=1, le=50
    ),
    location: str = Form("India", description="Job location"),
    resume_file: Optional[UploadFile] = File(
        None, description="Resume file (.pdf or .txt) for AI matching"
    ),
):
    """
    Start an async job scraping task.

    - Scrapes **Naukri** and **Foundit** for each profile
    - Optionally scores results against your resume using OpenAI
    - Returns a `task_id` — poll `/status/{task_id}` then fetch `/results/{task_id}`
    """
    profiles_list = [p.strip() for p in job_profiles.split(",") if p.strip()]
    if not profiles_list:
        raise HTTPException(status_code=400, detail="At least one job profile is required")

    # Unique task ID with microseconds to avoid collisions
    task_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    # Save resume temporarily (deleted after scraping finishes)
    resume_path = None
    if resume_file:
        if not resume_file.filename.endswith((".pdf", ".txt")):
            raise HTTPException(status_code=400, detail="Resume must be .pdf or .txt")
        resume_path = UPLOAD_DIR / f"{task_id}_{resume_file.filename}"
        with resume_path.open("wb") as buffer:
            shutil.copyfileobj(resume_file.file, buffer)

    # Register task
    task_status[task_id] = {
        "status": "processing",
        "started_at": datetime.now().isoformat(),
        "profiles": profiles_list,
        "total_jobs": 0,
    }

    # Kick off background scraping
    background_tasks.add_task(
        _dispatch_scraping,
        task_id=task_id,
        job_profiles=profiles_list,
        experience=experience,
        num_jobs=num_jobs,
        location=location,
        resume_path=str(resume_path) if resume_path else None,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )

    return JobSearchResponse(
        task_id=task_id,
        status="processing",
        message=f"Scraping started for {len(profiles_list)} profile(s)",
        profiles=profiles_list,
    )


@app.get("/status/{task_id}")
async def get_status(task_id: str):
    """Returns task status without the (potentially large) jobs payload."""
    if task_id not in task_status:
        raise HTTPException(status_code=404, detail="Task not found")
    # Strip jobs_data — use /results for the actual data
    return {k: v for k, v in task_status[task_id].items() if k != "jobs_data"}


@app.get("/results/{task_id}")
async def get_results(
    task_id: str,
    page: int = 1,
    page_size: int = 20,
):
    """
    Returns paginated job results as JSON.

    Query params:
    - `page` (default 1)
    - `page_size` (default 20)
    """
    if task_id not in task_status:
        raise HTTPException(status_code=404, detail="Task not found")

    task = task_status[task_id]

    if task["status"] == "processing":
        raise HTTPException(status_code=202, detail="Task is still processing — try again shortly")

    if task["status"] == "failed":
        raise HTTPException(
            status_code=500,
            detail=f"Task failed: {task.get('error', 'Unknown error')}"
        )

    jobs = task.get("jobs_data", [])
    total = len(jobs)
    start = (page - 1) * page_size

    return {
        "task_id": task_id,
        "total_jobs": total,
        "page": page,
        "page_size": page_size,
        "total_pages": max(1, (total + page_size - 1) // page_size),
        "profiles": task["profiles"],
        "jobs": jobs[start: start + page_size],
    }


@app.delete("/cleanup/{task_id}")
async def cleanup_task(task_id: str):
    """Remove a completed or failed task from memory."""
    if task_id not in task_status:
        raise HTTPException(status_code=404, detail="Task not found")

    if task_status[task_id]["status"] == "processing":
        raise HTTPException(status_code=400, detail="Cannot delete a running task")

    del task_status[task_id]
    return {"message": f"Task {task_id} removed successfully"}