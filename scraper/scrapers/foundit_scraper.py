
from scrapling.defaults import PlayWrightFetcher
from typing import List, Dict, Optional


class FounditScraper:
    """Scraper for Foundit.in using Scrapling PlayWrightFetcher"""

    def scrape(
        self,
        job_profile: str,
        location: str,
        experience: Optional[str],
        num_jobs: int,
        freshness: int = 1
    ) -> List[Dict]:
        jobs_data = []

        try:
            profile = job_profile.split(' ')
            job = '%20'.join(profile)
            search_job = '-'.join(profile)

            exp_min, exp_max = "0", "10"
            if experience and '-' in str(experience):
                exp_min, exp_max = experience.split('-')

            # Exact same URL structure as the working Selenium version
            url = (
                f"https://www.foundit.in/search/{search_job}-jobs?"
                f"start=1&limit={num_jobs}&query={job}&location={location}"
                f"&queryDerived=true"
                f"&jobFreshness={freshness}&experienceRanges={exp_min}~{exp_max}"
            )
            print(f"  🔍 URL: {url}")

            page = PlayWrightFetcher.fetch(
                url,
                headless=True,
                network_idle=False,
                disable_resources=False,
                timeout=60000,
                wait_selector=".jobCardWrapper",  # Wait until cards are in DOM — replaces time.sleep(5)
            )

            job_wrappers = list(page.css('.jobCardWrapper'))[:num_jobs]
            print(f"  Found {len(job_wrappers)} job listings")

            job_links = self._extract_job_links(job_wrappers)

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
        """Extract job titles and links from listing cards"""
        job_links = []
        for wrapper in job_wrappers:
            try:
                # Same structure as Selenium: jobCardTitle > a
                title_elem = wrapper.css_first('.jobCardTitle a')
                if title_elem:
                    title = title_elem.text.strip()
                    link = title_elem.attrib.get('href', '')
                    if title and link:
                        job_links.append({"title": title, "link": link})
            except Exception:
                continue
        return job_links

    def _extract_job_details(self, job_info: Dict) -> Optional[Dict]:
        """Visit individual job page and extract skills"""
        try:
            page = PlayWrightFetcher.fetch(
                job_info['link'],
                headless=True,
                network_idle=False,
                disable_resources=False,
                timeout=60000,
                wait_selector="#skillSectionNew",  # Wait for skills section — replaces time.sleep(3)
            )

            skills = []
            # Same as Selenium: find by ID skillSectionNew, then all <a> tags
            skill_section = page.css_first('#skillSectionNew')
            if skill_section:
                skill_tags = skill_section.css('a')
                skills = [tag.text.strip() for tag in skill_tags if tag.text.strip()]

            return {
                'Source': 'Foundit',
                'Job Title': job_info['title'],
                'Skills': ", ".join(skills) if skills else "N/A",
                'Job Link': job_info['link'],
            }

        except Exception as e:
            print(f"      Error extracting job details: {e}")
            return None