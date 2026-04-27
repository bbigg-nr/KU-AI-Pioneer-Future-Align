"""
jobthai_scraper.py
------------------
Scrapes Thai tech job listings from JobThai.com (server-rendered HTML).
Output: data/real_jobs.json

Run:
    python scraper/jobthai_scraper.py
"""

import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import re
import json
import time
import requests
from pathlib import Path
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "th-TH,th;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

SEARCH_TERMS = [
    "Data Scientist",
    "Machine Learning",
    "AI Engineer",
    "Software Engineer",
    "Data Analyst",
    "Backend Developer",
    "Full Stack",
    "DevOps",
    "Data Engineer",
]

SKILL_KEYWORDS = [
    "Python", "SQL", "R", "Java", "JavaScript", "TypeScript", "Go",
    "TensorFlow", "PyTorch", "Scikit-learn", "Keras",
    "Docker", "Kubernetes", "AWS", "GCP", "Azure",
    "Spark", "Hadoop", "Kafka", "Airflow",
    "React", "Node.js", "FastAPI", "Django", "Flask",
    "Machine Learning", "Deep Learning", "NLP", "Computer Vision",
    "MLOps", "DevOps", "CI/CD",
    "PostgreSQL", "MongoDB", "Redis",
    "Git", "Linux", "Agile", "Scrum",
    "Power BI", "Tableau",
    "Excel", "Statistics",
]

OUTPUT_PATH = Path("data/real_jobs.json")


def scrape_search_page(term: str, page: int = 1) -> list[dict]:
    """Scrape one search results page from JobThai."""
    url = f"https://www.jobthai.com/en/jobs"
    params = {"q": term, "page": page}

    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"  [!] Request failed: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    jobs = []

    # JobThai uses anchor tags for job cards
    cards = soup.select("a[href*='/job/']")
    if not cards:
        # Try generic job card selectors
        cards = soup.select("article, .job-item, [class*='job-card'], li a[href*='job']")

    print(f"  Found {len(cards)} cards on page {page}")

    seen_hrefs = set()
    for card in cards:
        href = card.get("href", "")
        if not href or href in seen_hrefs:
            continue
        seen_hrefs.add(href)

        text = card.get_text(separator="\n", strip=True)
        lines = [l for l in text.split("\n") if l.strip()]
        if len(lines) < 2:
            continue

        job_title = lines[0]
        company = lines[1] if len(lines) > 1 else "Unknown"

        # Skip non-job links (navigation etc.)
        if len(job_title) > 100 or len(job_title) < 3:
            continue

        # Extract salary
        salary_match = re.search(r"([\d,]+)\s*[-–]\s*([\d,]+)", text)
        salary = None
        if salary_match:
            try:
                salary = {
                    "min": int(salary_match.group(1).replace(",", "")),
                    "max": int(salary_match.group(2).replace(",", "")),
                }
            except ValueError:
                pass

        # Extract skills
        found_skills = [sk for sk in SKILL_KEYWORDS if sk.lower() in text.lower()]

        # Location
        locations = ["Bangkok", "Chiang Mai", "Remote", "Hybrid", "Phuket", "Khon Kaen"]
        location = next((loc for loc in locations if loc.lower() in text.lower()), "Bangkok")

        full_url = f"https://www.jobthai.com{href}" if href.startswith("/") else href

        jobs.append({
            "job_title": job_title,
            "search_term": term,
            "company": company,
            "location": location,
            "salary": salary,
            "skills_required": found_skills,
            "description": text[:600],
            "url": full_url,
            "source": "jobthai",
        })

    return jobs


def main():
    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    all_jobs = []

    for term in SEARCH_TERMS:
        print(f"\n[{term}]")
        for pg in range(1, 3):  # 2 pages per term
            jobs = scrape_search_page(term, page=pg)
            all_jobs.extend(jobs)
            if not jobs:
                break
            time.sleep(1.0)

        count = sum(1 for j in all_jobs if j["search_term"] == term)
        print(f"  => {count} jobs collected")

    # Deduplicate by URL
    seen = set()
    unique = []
    for j in all_jobs:
        key = j.get("url") or j.get("job_title")
        if key not in seen:
            seen.add(key)
            unique.append(j)

    OUTPUT_PATH.write_text(
        json.dumps(unique, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"\n=== Saved {len(unique)} unique jobs to {OUTPUT_PATH} ===")
    for term in SEARCH_TERMS:
        count = sum(1 for j in unique if j["search_term"] == term)
        print(f"  {term}: {count}")


if __name__ == "__main__":
    main()
