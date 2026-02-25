from typing import List, Optional
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
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

    def _load_resume(self):
        if self.resume_path:
            self.resume_content = read_resume(self.resume_path)
            print("✅ Resume loaded")
        else:
            print("ℹ️  No resume provided — AI scoring will be skipped")

    def _scrape_single(self, source: str, job_profile: str) -> List[dict]:
        """Scrape one source for one profile — runs in a thread"""
        if source == "naukri":
            return NaukriScraper().scrape(
                job_profile, self.location, self.experience, self.num_jobs
            )
        elif source == "foundit":
            return FounditScraper().scrape(
                job_profile, self.location, self.experience, self.num_jobs
            )
        return []

    def _scrape_all_sources(self):
        """
        Scrape all profiles x sources in parallel.
        e.g. 2 profiles x 2 sources = 4 threads running simultaneously.
        """
        tasks = [
            (source, profile)
            for profile in self.job_profiles
            for source in ["naukri", "foundit"]
        ]

        print(f"\n🚀 Scraping {len(tasks)} tasks in parallel...")

        with ThreadPoolExecutor(max_workers=len(tasks)) as executor:
            future_to_task = {
                executor.submit(self._scrape_single, source, profile): (source, profile)
                for source, profile in tasks
            }

            for future in as_completed(future_to_task):
                source, profile = future_to_task[future]
                try:
                    jobs = future.result()
                    self.all_jobs.extend(jobs)
                    print(f"  ✅ {source.capitalize()} / {profile}: {len(jobs)} jobs")
                except Exception as e:
                    print(f"  ❌ {source.capitalize()} / {profile}: {e}")

        print(f"\n🔢 Total jobs scraped: {len(self.all_jobs)}")

    def _score_and_rank(self):
        if not self.all_jobs:
            print("⚠️  No jobs to score")
            return

        if self.resume_content and self.openai_api_key:
            print("\n🤖 Running AI scoring...")
            self.all_jobs = AIScorer(self.openai_api_key).score_jobs(
                self.all_jobs, self.resume_content
            )
            print("✅ AI scoring complete")
        else:
            print("\n⚠️  Skipping AI scoring (no resume or API key)")
            for job in self.all_jobs:
                job["Match %"] = 0
                job["Matching Skills"] = "N/A"
                job["Missing Skills"] = "N/A"
                job["Match Reason"] = "No AI scoring available"

    def scrape_and_rank(self) -> List[dict]:
        """Main entry point — returns all jobs as a list, nothing written to disk."""
        self._load_resume()
        self._scrape_all_sources()
        self._score_and_rank()
        return self.all_jobs

    def get_total_jobs(self) -> int:
        return len(self.all_jobs)