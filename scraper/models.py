from pydantic import BaseModel, Field
from typing import List, Optional


class JobSearchRequest(BaseModel):
    """Request model for job search"""
    job_profiles: List[str] = Field(..., description="List of job profiles to search")
    experience: Optional[str] = Field(None, description="Experience level (e.g., '2-5')")
    num_jobs: int = Field(10, description="Number of jobs per profile", ge=1, le=50)
    location: str = Field("India", description="Job location")
    openai_api_key: Optional[str] = Field(None, description="OpenAI API key")


class JobSearchResponse(BaseModel):
    """Response model for job search"""
    task_id: str
    status: str
    message: str
    profiles: List[str]
    output_file: Optional[str] = None


class JobResult(BaseModel):
    """Model for individual job result"""
    source: str
    job_title: str
    skills: str
    job_link: str
    match_percentage: Optional[int] = None
    matching_skills: Optional[str] = None
    missing_skills: Optional[str] = None
    match_reason: Optional[str] = None