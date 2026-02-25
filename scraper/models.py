
from pydantic import BaseModel
from typing import List, Optional


class JobSearchResponse(BaseModel):
    task_id: str
    status: str
    message: str
    profiles: List[str]


class JobResult(BaseModel):
    Source: str
    Job_Title: str = ""
    Skills: str = "N/A"
    Match_Percent: int = 0
    Matching_Skills: str = "N/A"
    Missing_Skills: str = "N/A"
    Match_Reason: str = "N/A"
    Job_Link: str = ""