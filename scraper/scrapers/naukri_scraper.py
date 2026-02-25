
from scrapling.defaults import PlayWrightFetcher
from typing import List, Dict, Optional


class NaukriScraper:
    """Scraper for Naukri.com using Scrapling PlayWrightFetcher"""

    def scrape(
        self,
        job_profile: str,
        location: str,
        experience: Optional[str],
        num_jobs: int
    ) -> List[Dict]:
        jobs_data = []

        try:
            query = job_profile.lower().replace(' ', '-').replace('/', '-')
            loc_param = f"-in-{location.lower().replace(' ', '-')}" if location else ""

            exp_param = ""
            if experience and str(experience).strip():
                exp_range = str(experience).replace(' ', '')
                exp_param = f"&experience={exp_range}"

            url = f"https://www.naukri.com/{query}-jobs{loc_param}?jobAge=1{exp_param}"
            print(f"  🔍 URL: {url}")

            page = PlayWrightFetcher.fetch(
                url,
                headless=True,
                network_idle=True,
                disable_resources=False,  # Must be False — Naukri needs JS to render cards
                timeout=60000,            # 60s — Naukri is slow
            )

            # Try multiple selectors — Naukri changes class names periodically
            job_wrappers = (
                list(page.css('.srp-jobtuple-wrapper')) or
                list(page.css('article.jobTuple')) or
                list(page.css('.job-tuple-wrapper')) or
                list(page.css('[class*="jobTuple"]')) or
                list(page.css('[data-job-id]'))
            )
            job_wrappers = job_wrappers[:num_jobs]
            print(f"  Found {len(job_wrappers)} job listings")

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
        """Extract job title, link, and skills from a job card"""
        try:
            # Try multiple known title/link selectors
            link_elem = (
                wrapper.css_first('.row1 a') or
                wrapper.css_first('a.title') or
                wrapper.css_first('a.jobTitle') or
                wrapper.css_first('[class*="title"] a') or
                wrapper.css_first('h2 a') or
                wrapper.css_first('a[href*="naukri.com"]')
            )

            if not link_elem:
                return None

            title = link_elem.text.strip()
            link = link_elem.attrib.get('href', '')

            if not title or not link:
                return None

            # Try multiple known skill selectors
            skills = "N/A"
            skill_container = (
                wrapper.css_first('.row5') or
                wrapper.css_first('.tags-gt') or
                wrapper.css_first('[class*="skill"]') or
                wrapper.css_first('ul.tags')
            )
            if skill_container:
                items = skill_container.css('li') or skill_container.css('a')
                if items:
                    extracted = [s.text.strip() for s in items if s.text.strip()]
                    if extracted:
                        skills = ", ".join(extracted)

            return {
                'Source': 'Naukri',
                'Job Title': title,
                'Skills': skills,
                'Job Link': link,
            }

        except Exception as e:
            print(f"      Error extracting job details: {e}")
            return None