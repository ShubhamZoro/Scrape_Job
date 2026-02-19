from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import os
from datetime import datetime
import shutil
from pathlib import Path
from dotenv import load_dotenv
from scraper.job_scraper import JobScraper
from scraper.models import JobSearchRequest, JobSearchResponse
load_dotenv()
app = FastAPI(
    title="Job Scraper API",
    description="API for scraping and ranking job listings from Naukri and Foundit",
    version="1.0.0"
)

# Create directories for uploads and outputs
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Store background tasks status
task_status = {}


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Job Scraper API",
        "version": "1.0.0",
        "endpoints": {
            "POST /scrape": "Start job scraping process",
            "GET /status/{task_id}": "Check scraping status",
            "GET /results/{task_id}": "Get scraped jobs as JSON",
            "GET /download/{filename}": "Download results file (Excel)",
            "GET /health": "Health check"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.post("/scrape", response_model=JobSearchResponse)
async def scrape_jobs(
    background_tasks: BackgroundTasks,
    job_profiles: str = Form(..., description="Comma-separated job profiles (e.g., 'Data Scientist,ML Engineer')"),
    experience: Optional[str] = Form(None, description="Experience level (e.g., '2-5' or '3')"),
    num_jobs: int = Form(10, description="Number of jobs to scrape per profile"),
    location: str = Form("India", description="Job location"),
    resume_file: Optional[UploadFile] = File(None, description="Resume file (.pdf or .txt)")
):
    """
    Scrape jobs from Naukri and Foundit with AI-powered ranking
    
    - **job_profiles**: Comma-separated list of job titles to search
    - **experience**: Experience level (e.g., '2-5' or '3')
    - **num_jobs**: Number of jobs to fetch per profile per source
    - **location**: Location for job search
    - **resume_file**: Upload your resume for AI matching (optional)
    - **openai_api_key**: OpenAI API key for scoring (optional)
    """
    
    try:
        # Generate task ID
        task_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Parse job profiles
        profiles_list = [p.strip() for p in job_profiles.split(',') if p.strip()]
        
        if not profiles_list:
            raise HTTPException(status_code=400, detail="At least one job profile is required")
        
        # Handle resume file upload
        resume_path = None
        if resume_file:
            resume_filename = f"{task_id}_{resume_file.filename}"
            resume_path = UPLOAD_DIR / resume_filename
            
            with resume_path.open("wb") as buffer:
                shutil.copyfileobj(resume_file.file, buffer)
        
        # Initialize task status
        task_status[task_id] = {
            "status": "processing",
            "started_at": datetime.now().isoformat(),
            "profiles": profiles_list,
            "total_jobs": 0
        }
        
        # Run scraping in background
        background_tasks.add_task(
            run_scraping_task,
            task_id=task_id,
            job_profiles=profiles_list,
            experience=experience,
            num_jobs=num_jobs,
            location=location,
            resume_path=str(resume_path) if resume_path else None,
            openai_api_key= os.getenv('OPENAI_API_KEY')
        )
        
        return JobSearchResponse(
            task_id=task_id,
            status="processing",
            message=f"Scraping started for {len(profiles_list)} job profile(s)",
            profiles=profiles_list
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting scraping: {str(e)}")


async def run_scraping_task(
    task_id: str,
    job_profiles: List[str],
    experience: Optional[str],
    num_jobs: int,
    location: str,
    resume_path: Optional[str],
    openai_api_key: Optional[str]
):
    """Background task to run job scraping"""
    
    try:
        scraper = JobScraper(
            job_profiles=job_profiles,
            experience=experience,
            num_jobs=num_jobs,
            location=location,
            resume_path=resume_path,
            openai_api_key=openai_api_key
        )
        
        # Run scraping
        output_file, jobs_data = scraper.scrape_and_rank()
        
        # Move output file to outputs directory
        if output_file and os.path.exists(output_file):
            new_filename = f"{task_id}_ranked_jobs.xlsx"
            new_path = OUTPUT_DIR / new_filename
            shutil.move(output_file, new_path)
            
            task_status[task_id].update({
                "status": "completed",
                "completed_at": datetime.now().isoformat(),
                "output_file": new_filename,
                "total_jobs": scraper.get_total_jobs(),
                "jobs_data": jobs_data  # Store the jobs data
            })
        else:
            task_status[task_id].update({
                "status": "failed",
                "completed_at": datetime.now().isoformat(),
                "error": "No jobs found"
            })
            
    except Exception as e:
        task_status[task_id].update({
            "status": "failed",
            "completed_at": datetime.now().isoformat(),
            "error": str(e)
        })
    
    finally:
        # Cleanup resume file
        if resume_path and os.path.exists(resume_path):
            os.remove(resume_path)


@app.get("/status/{task_id}")
async def get_status(task_id: str):
    """Get the status of a scraping task"""
    
    if task_id not in task_status:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return task_status[task_id]


@app.get("/results/{task_id}")
async def get_results(task_id: str):
    """Get the scraped jobs as JSON"""
    
    if task_id not in task_status:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task_status[task_id]["status"] != "completed":
        raise HTTPException(
            status_code=400, 
            detail=f"Task not completed yet. Current status: {task_status[task_id]['status']}"
        )
    
    if "jobs_data" not in task_status[task_id]:
        raise HTTPException(status_code=404, detail="Job data not found")
    
    return {
        "task_id": task_id,
        "total_jobs": task_status[task_id]["total_jobs"],
        "profiles": task_status[task_id]["profiles"],
        "jobs": task_status[task_id]["jobs_data"]
    }


@app.get("/download/{filename}")
async def download_file(filename: str):
    """Download the results file"""
    
    file_path = OUTPUT_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@app.delete("/cleanup/{task_id}")
async def cleanup_task(task_id: str):
    """Clean up task data and associated files"""
    
    if task_id not in task_status:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Remove output file if exists
    if "output_file" in task_status[task_id]:
        output_file = OUTPUT_DIR / task_status[task_id]["output_file"]
        if output_file.exists():
            os.remove(output_file)
    
    # Remove task status
    del task_status[task_id]
    
    return {"message": f"Task {task_id} cleaned up successfully"}


# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)
