from openai import OpenAI
from typing import List, Dict
import json
import time


class AIScorer:
    """AI-powered job matching scorer using OpenAI API"""
    
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        
    def score_jobs(self, jobs: List[Dict], resume_content: str) -> List[Dict]:
        """
        Score all jobs against the resume
        
        Args:
            jobs: List of job dictionaries
            resume_content: Resume text content
            
        Returns:
            List of jobs with scoring information, sorted by match percentage
        """
        print(f"\n🤖 AI Scoring {len(jobs)} jobs against resume...")
        
        scored_jobs = []
        
        for idx, job in enumerate(jobs, 1):
            # print(f"  Analyzing {idx}/{len(jobs)}: {job['Job Title'][:40]}...", end='')
            
            result = self._calculate_match_score(
                job['Job Title'],
                job['Skills'],
                resume_content
            )
            
            # Add scoring fields to job
            job['Match %'] = result['match_percentage']
            job['Matching Skills'] = ', '.join(result['matching_skills']) if result['matching_skills'] else 'None'
            job['Missing Skills'] = ', '.join(result['missing_skills']) if result['missing_skills'] else 'None'
            job['Match Reason'] = result['brief_reason']
            
            scored_jobs.append(job)
            # print(f" ✓ {result['match_percentage']}%")
            
            # Rate limiting delay
            time.sleep(0.5)
        
        # Sort by match percentage (highest first)
        scored_jobs.sort(key=lambda x: x['Match %'], reverse=True)
        
        # print(f"\n✅ AI scoring complete! Jobs ranked by match percentage.")
        
        return scored_jobs
    
    def _calculate_match_score(
        self,
        job_title: str,
        job_skills: str,
        resume_content: str
    ) -> Dict:
        """
        Calculate match score for a single job
        
        Args:
            job_title: Job title
            job_skills: Required skills for the job
            resume_content: Resume text
            
        Returns:
            Dictionary with match_percentage, matching_skills, missing_skills, brief_reason
        """
        
        prompt = f"""Analyze the match between this job and the candidate's resume.

Job Title: {job_title}
Required Skills: {job_skills}

Candidate Resume:
{resume_content}

Provide ONLY a JSON response with this exact structure (no markdown, no extra text):
{{
  "match_percentage": <number between 0-100>,
  "matching_skills": ["skill1", "skill2"],
  "missing_skills": ["skill3", "skill4"],
  "brief_reason": "2-3 sentence explanation"
}}

Be strict but fair in your assessment. Consider:
1. Direct skill matches
2. Related/transferable skills
3. Experience level alignment
4. Domain knowledge overlap"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert recruiter analyzing job-candidate fit. Always respond with valid JSON only."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Clean up response (remove markdown if present)
            response_text = response_text.replace('```json', '').replace('```', '').strip()
            
            result = json.loads(response_text)
            return result
            
        except Exception as e:
            print(f" ⚠️ Error: {e}")
            return {
                "match_percentage": 0,
                "matching_skills": [],
                "missing_skills": [],
                "brief_reason": "Error calculating match"
            }