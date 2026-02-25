from scrapling.defaults import PlayWrightFetcher
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed


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

            url = (
                f"https://www.foundit.in/search/{search_job}-jobs?"
                f"start=1&limit={num_jobs}&query={job}&location={location}"
                f"&queryDerived=true"
                f"&jobFreshness={freshness}&experienceRanges={exp_min}~{exp_max}"
            )
            print(f"  🔍 URL: {url}")

            # Step 1: Fetch listing page
            page = PlayWrightFetcher.fetch(
                url,
                headless=True,
                network_idle=False,
                disable_resources=False,
                timeout=60000,
                wait_selector=".jobCardWrapper",
            )

            job_wrappers = list(page.css('.jobCardWrapper'))[:num_jobs]
            print(f"  Found {len(job_wrappers)} job listings")

            job_links = self._extract_job_links(job_wrappers)

            # Step 2: Fetch all detail pages IN PARALLEL
            jobs_data = self._fetch_details_parallel(job_links)

        except Exception as e:
            print(f"  ❌ Error scraping Foundit: {e}")

        return jobs_data

    def _extract_job_links(self, job_wrappers) -> List[Dict]:
        job_links = []
        for wrapper in job_wrappers:
            try:
                title_elem = wrapper.css_first('.jobCardTitle a')
                if title_elem:
                    title = title_elem.text.strip()
                    link = title_elem.attrib.get('href', '')
                    if title and link:
                        job_links.append({"title": title, "link": link})
            except Exception:
                continue
        return job_links

    def _fetch_details_parallel(self, job_links: List[Dict]) -> List[Dict]:
        """Fetch all job detail pages concurrently instead of one by one"""
        results = []

        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_job = {
                executor.submit(self._extract_job_details, job_info): job_info
                for job_info in job_links
            }

            for idx, future in enumerate(as_completed(future_to_job), 1):
                job_info = future_to_job[future]
                try:
                    job_data = future.result()
                    if job_data:
                        results.append(job_data)
                        print(f"    ✓ Job {idx}: {job_data['Job Title'][:50]}")
                except Exception as e:
                    print(f"    ✗ Error fetching {job_info['title'][:40]}: {e}")

        return results

    def _extract_job_details(self, job_info: Dict) -> Optional[Dict]:
        try:
            page = PlayWrightFetcher.fetch(
                job_info['link'],
                headless=True,
                network_idle=False,
                disable_resources=False,
                timeout=60000,
                wait_selector="#skillSectionNew",
            )

            skills = []
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