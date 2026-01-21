#  Job Scraper

Scrape job from naukri and foundit and rank them based on your resume.



---

## API Endpoints

### Scrape
- `POST /api/auth/register` - Scrape jobs


---

## Job Scoring Algorithm

Jobs are scored on 5 weighted components:
- **Semantic Match (30%)**: Vector similarity between your profile and job description
- **Skill Match (30%)**: Percentage of required skills you have
- **Experience Match (20%)**: Years of experience alignment
- **Location Match (10%)**: Location preference alignment

---



