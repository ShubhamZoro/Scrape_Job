
from typing import List, Optional
import os
from .scrapers.naukri_scraper import NaukriScraper
from .scrapers.foundit_scraper import FounditScraper
from .ai_scorer import AIScorer
from .utils import read_resume


class JobScraper:
    """Orchestrates scraping from all sources and AI scoring"""

    def __init__(
        self,
        job_profiles: List[str],
        experience: Optional[str] = None,
        num_jobs: int = 10,
        location: str = "India",
        resume_path: Optional[str] = None,
        openai_api_key: Optional[str] = None,
    ):
        self.job_profiles = job_profiles
        self.experience = experience
        self.num_jobs = num_jobs
        self.location = location
        self.resume_path = resume_path
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")

        self.all_jobs: List[dict] = []
        self.resume_content: Optional[str] = None

    # ── Private ───────────────────────────────────────────────────────────────

    def _load_resume(self):
        """Load resume text content if a path was provided"""
        if self.resume_path:
            self.resume_content = read_resume(self.resume_path)
            print("✅ Resume loaded")
        else:
            print("ℹ️  No resume provided — AI scoring will be skipped")

    def _scrape_all_sources(self):
        """Scrape jobs from Naukri and Foundit for every job profile"""
        for job_profile in self.job_profiles:
            print(f"\n{'─' * 60}")
            print(f"  Scraping: {job_profile}")
            print(f"{'─' * 60}")

            # Naukri
            print("\n📍 Scraping NAUKRI...")
            naukri_jobs = NaukriScraper().scrape(
                job_profile, self.location, self.experience, self.num_jobs
            )
            self.all_jobs.extend(naukri_jobs)
            print(f"   ✅ {len(naukri_jobs)} jobs from Naukri")

            # Foundit
            print("\n📍 Scraping FOUNDIT...")
            foundit_jobs = FounditScraper().scrape(
                job_profile, self.location, self.experience, self.num_jobs
            )
            self.all_jobs.extend(foundit_jobs)
            print(f"   ✅ {len(foundit_jobs)} jobs from Foundit")

        print(f"\n🔢 Total jobs scraped: {len(self.all_jobs)}")

    def _score_and_rank(self):
        """Score jobs using AI if resume and API key are available"""
        if not self.all_jobs:
            print("⚠️  No jobs to score")
            return

        if self.resume_content and self.openai_api_key:
            print("\n🤖 Running AI scoring...")
            ai_scorer = AIScorer(self.openai_api_key)
            self.all_jobs = ai_scorer.score_jobs(self.all_jobs, self.resume_content)
            print("✅ AI scoring complete")
        else:
            print("\n⚠️  Skipping AI scoring (no resume or API key)")
            for job in self.all_jobs:
                job["Match %"] = 0
                job["Matching Skills"] = "N/A"
                job["Missing Skills"] = "N/A"
                job["Match Reason"] = "No AI scoring available"

    # ── Public ────────────────────────────────────────────────────────────────

    def scrape_and_rank(self) -> List[dict]:
        """
        Main entry point — scrape, score, and return jobs as a list.
        No files are written to disk.
        """
        self._load_resume()
        self._scrape_all_sources()
        self._score_and_rank()
        return self.all_jobs

    def get_total_jobs(self) -> int:
        return len(self.all_jobs)