from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from typing import List, Optional, Dict
import pandas as pd
from datetime import datetime
import os
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from .scrapers.naukri_scraper import NaukriScraper
from .scrapers.foundit_scraper import FounditScraper
from .ai_scorer import AIScorer
from .utils import read_resume


class JobScraper:
    """Main job scraper class that orchestrates the scraping process"""
    
    def __init__(
        self,
        job_profiles: List[str],
        experience: Optional[str] = None,
        num_jobs: int = 10,
        location: str = "India",
        resume_path: Optional[str] = None,
        openai_api_key: Optional[str] = None
    ):
        self.job_profiles = job_profiles
        self.experience = experience
        self.num_jobs = num_jobs
        self.location = location
        self.resume_path = resume_path
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        
        self.driver = None
        self.all_jobs = []
        self.resume_content = None
        
    def setup_driver(self):
        """Setup Chrome driver with headless options"""
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument(
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=chrome_options)
        #print("✅ Chrome driver initialized")
        
    def load_resume(self):
        """Load resume content if provided"""
        if self.resume_path:
            self.resume_content = read_resume(self.resume_path)
        else:
            print("ℹ️ No resume provided - AI scoring will be skipped")
            
    def scrape_all_sources(self):
        """Scrape jobs from all sources"""
        # print(f"\n{'=' * 70}")
        # print(f"SCRAPING JOBS")
        # print(f"{'=' * 70}")
        # print(f"📋 Job Profiles: {', '.join(self.job_profiles)}")
        # print(f"📍 Location: {self.location}")
        # print(f"💼 Experience: {self.experience or 'Not specified'}")
        # print(f"🔢 Jobs per profile: {self.num_jobs}")
        
        for job_profile in self.job_profiles:
            # print(f"\n{'─' * 70}")
            # print(f"Scraping: {job_profile}")
            # print(f"{'─' * 70}")
            
            # # Scrape Naukri
            # print("\n📍 Scraping NAUKRI...")
            naukri_scraper = NaukriScraper(self.driver)
            naukri_jobs = naukri_scraper.scrape(
                job_profile, self.location, self.experience, self.num_jobs
            )
            self.all_jobs.extend(naukri_jobs)
            # print(f"   Found {len(naukri_jobs)} jobs from Naukri")
            
            # # Scrape Foundit
            # print("\n📍 Scraping FOUNDIT...")
            foundit_scraper = FounditScraper(self.driver)
            foundit_jobs = foundit_scraper.scrape(
                job_profile, self.location, self.experience, self.num_jobs
            )
            self.all_jobs.extend(foundit_jobs)
        #     print(f"   Found {len(foundit_jobs)} jobs from Foundit")
        
        # print(f"\n✅ Total jobs scraped: {len(self.all_jobs)}")
        
    def score_and_rank_jobs(self):
        """Score jobs using AI and rank them"""
        if not self.all_jobs:
            # print("⚠️ No jobs to score")
            return
        
        if self.resume_content and self.openai_api_key:
            ai_scorer = AIScorer(self.openai_api_key)
            self.all_jobs = ai_scorer.score_jobs(self.all_jobs, self.resume_content)
        else:
            # print("\n⚠️ Skipping AI scoring (no resume or API key provided)")
            # Add default scoring fields
            for job in self.all_jobs:
                job['Match %'] = 0
                job['Matching Skills'] = 'N/A'
                job['Missing Skills'] = 'N/A'
                job['Match Reason'] = 'No AI scoring available'
    
    def save_results(self) -> str:
        """Save results to Excel file"""
        if not self.all_jobs:
            # print("⚠️ No jobs to save")
            return None
        
        df = pd.DataFrame(self.all_jobs)
        
        # Reorder columns
        column_order = [
            'Match %', 'Source', 'Job Title', 'Skills', 
            'Matching Skills', 'Missing Skills', 'Match Reason', 'Job Link'
        ]
        df = df[column_order]
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f'jobs_ranked_{timestamp}.xlsx'
        
        # Save to Excel
        df.to_excel(filename, index=False, sheet_name='Ranked Jobs')
        
        print(f"\n✅ Results saved to '{filename}'")
        
        # # Show top matches
        # if self.resume_content and self.openai_api_key:
        #     # print(f"\n🏆 Top 5 Matches:")
        #     for i, job in enumerate(self.all_jobs[:5], 1):
        #         print(f"  {i}. {job['Match %']}% - {job['Job Title'][:60]}")
        
        return filename
    
    def scrape_and_rank(self) -> tuple:
        """Main method to scrape, score, and save jobs - returns (filename, jobs_data)"""
        try:
            self.setup_driver()
            self.load_resume()
            self.scrape_all_sources()
            self.score_and_rank_jobs()
            output_file = self.save_results()
            
            # Return both the file and the jobs data
            return output_file, self.all_jobs
            
        finally:
            if self.driver:
                self.driver.quit()
                # print("\n🔒 Browser closed")
    
    def get_total_jobs(self) -> int:
        """Get total number of jobs scraped"""
        return len(self.all_jobs)