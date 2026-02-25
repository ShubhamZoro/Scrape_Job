"""
Example: Get scraped jobs as JSON instead of Excel file
"""

import requests
import time
import json
from pathlib import Path
import time

start = time.perf_counter()
BASE_URL = "http://localhost:8000/"

# Prepare data
data = {
    'job_profiles': 'Data Scientist,ML Engineer',
    'experience': '3-5',
    'num_jobs': 5,
    'location': 'India'
}

# Optional: Add resume
resume_path = Path(r'Resume.pdf')
files = None
if resume_path.exists():
    files = {'resume_file': open(resume_path, 'rb')}
    print(f"✅ Resume loaded: {resume_path.name}")

# Start scraping
print("\n🚀 Starting job scraping...")
response = requests.post(f'{BASE_URL}/scrape', data=data, files=files)

if files:
    files['resume_file'].close()

result = response.json()
task_id = result['task_id']
print(f"Task ID: {task_id}")

# Wait for completion
print("\n⏳ Waiting for completion...")
while True:
    status_response = requests.get(f'{BASE_URL}/status/{task_id}')
    status = status_response.json()
    
    print(f"Status: {status['status']}", end='\r')
    
    if status['status'] == 'completed':
        print(f"\n✅ Completed! Total jobs: {status['total_jobs']}")
        break
    elif status['status'] == 'failed':
        print(f"\n❌ Failed: {status.get('error')}")
        exit(1)
    
    time.sleep(5)

# Get results as JSON
print("\n📥 Fetching results as JSON...")
results_response = requests.get(f'{BASE_URL}/results/{task_id}')
results = results_response.json()
print(results)
end = time.perf_counter()
print(f"Time taken: {end - start:.3f} seconds")

# print(f"\n{'='*70}")
# print(f"SCRAPED JOBS - JSON FORMAT")
# print(f"{'='*70}")
# print(f"Total Jobs: {results['total_jobs']}")
# print(f"Profiles: {', '.join(results['profiles'])}")

# # Display top 5 jobs
# print(f"\n🏆 Top 5 Matches:")
# for i, job in enumerate(results['jobs'][:5], 1):
#     print(f"\n{i}. {job['Job Title']}")
#     print(f"   Match: {job['Match %']}%")
#     print(f"   Source: {job['Source']}")
#     print(f"   Skills: {job['Skills'][:80]}...")
#     print(f"   Link: {job['Job Link'][:60]}...")

# # Save to JSON file (optional)
# output_filename = f"jobs_{task_id}.json"
# with open(output_filename, 'w', encoding='utf-8') as f:
#     json.dump(results, f, indent=2, ensure_ascii=False)
# print(f"\n💾 Saved to: {output_filename}")

# # You can also still download the Excel file if needed
# print(f"\n📄 Excel file available at:")
# print(f"   {BASE_URL}/download/{status['output_file']}")

# # Example: Download Excel file too
# download_response = requests.get(f"{BASE_URL}/download/{status['output_file']}")
# with open(status['output_file'], 'wb') as f:
#     f.write(download_response.content)
# print(f"   Downloaded: {status['output_file']}")

# print("\n✅ Done!")