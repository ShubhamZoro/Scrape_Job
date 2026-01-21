from selenium.webdriver.common.by import By
from typing import List, Dict, Optional
import time


class NaukriScraper:
    """Scraper for Naukri.com"""
    
    def __init__(self, driver):
        self.driver = driver
        
    def scrape(
        self,
        job_profile: str,
        location: str,
        experience: Optional[str],
        num_jobs: int
    ) -> List[Dict]:
        """
        Scrape jobs from Naukri.com
        
        Args:
            job_profile: Job title to search for
            location: Location for job search
            experience: Experience level
            num_jobs: Number of jobs to scrape
            
        Returns:
            List of job dictionaries
        """
        jobs_data = []
        
        try:
            # Build URL
            query = job_profile.lower().replace(' ', '-').replace('/', '-')
            loc_param = f"-in-{location.lower().replace(' ', '-')}" if location else ""
            
            exp_param = ""
            if experience and str(experience).strip():
                if '-' in str(experience):
                    exp_range = str(experience).replace(' ', '')
                    exp_param = f"&experience={exp_range}"
                else:
                    exp_param = f"&experience={experience}"
            
            url = f"https://www.naukri.com/{query}-jobs{loc_param}?jobAge=1{exp_param}"
            
            print(f"  🔍 URL: {url}")
            
            # Load page
            self.driver.get(url)
            time.sleep(5)
            
            # Scroll to load more jobs
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(2)
            
            # Find job cards
            job_wrappers = self.driver.find_elements(By.CLASS_NAME, "srp-jobtuple-wrapper")[:num_jobs]
            
            print(f"  Found {len(job_wrappers)} job listings")
            
            # Extract job details
            for i, wrapper in enumerate(job_wrappers, 1):
                try:
                    job_data = self._extract_job_details(wrapper)
                    if job_data:
                        jobs_data.append(job_data)
                        print(f"    ✓ Job {i}: {job_data['Job Title'][:50]}")
                except Exception as e:
                    print(f"    ✗ Error extracting job {i}: {e}")
        
        except Exception as e:
            print(f"  ❌ Error scraping Naukri: {e}")
        
        return jobs_data
    
    def _extract_job_details(self, wrapper) -> Optional[Dict]:
        """Extract details from a job card wrapper"""
        try:
            # Get job title and link
            row1_div = wrapper.find_element(By.CLASS_NAME, "row1")
            job_link_elem = row1_div.find_element(By.TAG_NAME, "a")
            title = job_link_elem.text.strip()
            link = job_link_elem.get_attribute("href")
            
            # Get skills
            skills = "N/A"
            try:
                row5_div = wrapper.find_element(By.CLASS_NAME, "row5")
                skill_items = row5_div.find_elements(By.TAG_NAME, "li")
                if skill_items:
                    skills = ", ".join([
                        item.text.strip() 
                        for item in skill_items 
                        if item.text.strip()
                    ])
            except:
                pass
            
            return {
                'Source': 'Naukri',
                'Job Title': title,
                'Skills': skills,
                'Job Link': link,
            }
            
        except Exception as e:
            print(f"      Error extracting job details: {e}")
            return None