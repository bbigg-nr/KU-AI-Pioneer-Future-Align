import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

"""
jobtopgun_scraper.py
--------------------
Scrapes real Thai tech job listings from Jobtopgun using Playwright.
Output: data/real_jobs.json

Run:
    python scraper/jobtopgun_scraper.py
"""

import asyncio
import json
import re
import time
from pathlib import Path
from playwright.async_api import async_playwright

SEARCH_TERMS = [
    "Data Scientist",
    "Machine Learning Engineer",
    "AI Engineer",
    "Software Engineer",
    "Data Analyst",
    "Backend Developer",
    "Full Stack Developer",
    "DevOps Engineer",
    "Cybersecurity",
]

JOBS_PER_TERM = 10
OUTPUT_PATH = Path("data/real_jobs.json")


async def scrape_jobs(term: str, page, max_jobs: int) -> list[dict]:
    """Search Jobtopgun for a term and extract job listings."""
    jobs = []

    url = f"https://www.jobtopgun.com/search?keyword={term.replace(' ', '+')}"
    print(f"  → Fetching: {url}")

    try:
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(2000)
    except Exception as e:
        print(f"  ✗ Failed to load page: {e}")
        return jobs

    # Try to find job cards by looking for common patterns
    # Jobtopgun renders job list items — look for anchor tags inside list containers
    job_cards = await page.query_selector_all("a[href*='/job/'], a[href*='/jobs/'], li.job-item, div.job-card, article")

    if not job_cards:
        # Fallback: look for any container with job-like text
        job_cards = await page.query_selector_all("[class*='job'], [class*='Job'], [class*='position']")

    print(f"  Found {len(job_cards)} potential cards")

    for card in job_cards[:max_jobs]:
        try:
            text = await card.inner_text()
            href = await card.get_attribute("href") or ""

            if len(text.strip()) < 10:
                continue

            lines = [l.strip() for l in text.split("\n") if l.strip()]
            if not lines:
                continue

            # Heuristic extraction
            job_title = lines[0] if lines else term
            company = lines[1] if len(lines) > 1 else "Unknown"

            # Extract salary (Thai baht patterns)
            salary_match = re.search(r"(\d[\d,]+)\s*[-–]\s*(\d[\d,]+)", text)
            salary = {
                "min": int(salary_match.group(1).replace(",", "")),
                "max": int(salary_match.group(2).replace(",", ""))
            } if salary_match else None

            # Extract location
            locations = ["Bangkok", "กรุงเทพ", "Remote", "Hybrid", "Chiang Mai", "เชียงใหม่"]
            location = next((loc for loc in locations if loc.lower() in text.lower()), "Bangkok")

            # Extract skills from text (common tech keywords)
            skill_keywords = [
                "Python", "SQL", "R", "Java", "JavaScript", "TypeScript", "Go", "Rust",
                "TensorFlow", "PyTorch", "Keras", "Scikit-learn",
                "Docker", "Kubernetes", "AWS", "GCP", "Azure",
                "Spark", "Hadoop", "Kafka", "Airflow",
                "React", "Node.js", "FastAPI", "Django", "Flask",
                "Machine Learning", "Deep Learning", "NLP", "Computer Vision",
                "Data Engineering", "MLOps", "DevOps", "CI/CD",
                "PostgreSQL", "MongoDB", "Redis", "Elasticsearch",
                "Git", "Linux", "Agile", "Scrum",
                "Power BI", "Tableau", "Looker",
            ]
            found_skills = [sk for sk in skill_keywords if sk.lower() in text.lower()]

            job = {
                "job_title": job_title,
                "search_term": term,
                "company": company,
                "location": location,
                "salary": salary,
                "skills_required": found_skills,
                "description": text[:800],
                "url": f"https://www.jobtopgun.com{href}" if href.startswith("/") else href,
                "source": "jobtopgun",
            }
            jobs.append(job)

        except Exception as e:
            print(f"  ✗ Card parse error: {e}")
            continue

    return jobs


async def main():
    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    all_jobs = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
            locale="th-TH",
        )
        page = await context.new_page()

        for term in SEARCH_TERMS:
            print(f"\n[{term}]")
            jobs = await scrape_jobs(term, page, JOBS_PER_TERM)
            all_jobs.extend(jobs)
            print(f"  ✓ Got {len(jobs)} jobs")
            await asyncio.sleep(1.5)  # polite delay

        await browser.close()

    # Deduplicate by url
    seen = set()
    unique_jobs = []
    for j in all_jobs:
        key = j.get("url") or j.get("job_title")
        if key not in seen:
            seen.add(key)
            unique_jobs.append(j)

    OUTPUT_PATH.write_text(json.dumps(unique_jobs, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✅ Saved {len(unique_jobs)} unique jobs → {OUTPUT_PATH}")

    # Quick stats
    for term in SEARCH_TERMS:
        count = sum(1 for j in unique_jobs if j["search_term"] == term)
        print(f"  {term}: {count}")


if __name__ == "__main__":
    asyncio.run(main())
