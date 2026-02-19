from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from typing import List, Dict, Optional
import time


class FounditScraper:
    """Scraper for Foundit.in"""
    
    def __init__(self, driver):
        self.driver = driver
        
    def scrape(
        self,
        job_profile: str,
        location: str,
        experience: Optional[str],
        num_jobs: int,
        freshness: int = 1
    ) -> List[Dict]:
        """
        Scrape jobs from Foundit.in
        
        Args:
            job_profile: Job title to search for
            location: Location for job search
            experience: Experience level
            num_jobs: Number of jobs to scrape
            freshness: Job freshness in days (default: 1)
            
        Returns:
            List of job dictionaries
        """
        jobs_data = []
        profile=job_profile.split(' ')
        job='%20'.join(profile)
        search_job='-'.join(profile)
        
        try:
            # Build URL
            url = (
                f"https://www.foundit.in/search/{search_job}-jobs?"
                f"start=1&limit={num_jobs}&query={job}&location={location}"
                f"&queryDerived=true&jobCities={location}"
            )
            
            exp_min, exp_max = experience.split('-')
            url += f"&jobFreshness={freshness}"
            url += f"&experienceRanges={exp_min}~{exp_max}"
            
           
            
            print(f"  🔍 URL: {url}")
            
            # Load page
            self.driver.get(url)
            time.sleep(5)
            
            # Find job cards and extract links
            job_wrappers = self.driver.find_elements(By.CLASS_NAME, "jobCardWrapper")[:num_jobs]
            print(f"  Found {len(job_wrappers)} job listings")
            
            job_links = self._extract_job_links(job_wrappers)
            
            # Visit each job page to get details
            for idx, job_info in enumerate(job_links, 1):
                try:
                    job_data = self._extract_job_details(job_info)
                    if job_data:
                        jobs_data.append(job_data)
                        print(f"    ✓ Job {idx}: {job_data['Job Title'][:50]}")
                except Exception as e:
                    print(f"    ✗ Error extracting job {idx}: {e}")
        
        except Exception as e:
            print(f"  ❌ Error scraping Foundit: {e}")
        
        return jobs_data
    
    def _extract_job_links(self, job_wrappers) -> List[Dict]:
        """Extract job titles and links from job cards"""
        job_links = []
        
        for wrapper in job_wrappers:
            try:
                h2_element = wrapper.find_element(By.CLASS_NAME, "jobCardTitle")
                a_tag = h2_element.find_element(By.TAG_NAME, "a")
                job_title = a_tag.text.strip()
                job_link = a_tag.get_attribute("href")
                
                if job_title and job_link:
                    job_links.append({
                        "title": job_title,
                        "link": job_link
                    })
            except NoSuchElementException:
                continue
        
        return job_links
    
    def _extract_job_details(self, job_info: Dict) -> Optional[Dict]:
        """Visit job page and extract detailed information"""
        try:
            # Navigate to job page
            self.driver.get(job_info['link'])
            time.sleep(3)
            
            # Extract skills
            skills = []
            try:
                key_skills_section = self.driver.find_element(By.ID, "skillSectionNew")
                skill_tags = key_skills_section.find_elements(By.TAG_NAME, "a")
                skills = [
                    skill.text.strip() 
                    for skill in skill_tags 
                    if skill.text.strip()
                ]
            except NoSuchElementException:
                pass
            
            return {
                'Source': 'Foundit',
                'Job Title': job_info['title'],
                'Skills': ", ".join(skills) if skills else "N/A",
                'Job Link': job_info['link'],
            }
            
        except Exception as e:
            print(f"      Error extracting job details: {e}")
            return None
