# -*- coding: utf-8 -*-
"""
generate_backtest_data.py
--------------------------
สร้าง holdout test set สำหรับ Backtesting ที่ไม่มี data leakage

หลักการ:
  - เลือก 10 job titles ที่หลากหลาย
  - แต่ละ job สร้าง 10 profiles (รวม 100 profiles)
  - แต่ละ profile มี skill เพียง 60-80% ของที่ job ต้องการ (simulate ความไม่สมบูรณ์)
  - เพิ่ม noise skills 0-2 อัน (simulate skills ที่ไม่เกี่ยว)
  - assign levels แบบสุ่ม (ไม่ match job requirement ทุกอัน)

Output: data/backtest_alumni.csv
รัน:    python generate_backtest_data.py
"""

import csv
import json
import random
import collections

LABOR_MARKET_PATH = "data/labor_market_dataset_with_salary.csv"
OUTPUT_PATH       = "data/backtest_alumni.csv"

RANDOM_SEED       = 99   # ต่างจาก seed ของ dataset เดิม (42)
random.seed(RANDOM_SEED)

LEVELS = ["Beginner", "Intermediate", "Advanced"]

# job titles ที่ใช้ทดสอบ — เลือกให้ครอบคลุมหลาย sector
TARGET_JOBS = [
    "AI/ML Engineer",
    "Backend Engineer",
    "Blockchain / Web3 Developer",
    "Cloud Architect",
    "Cybersecurity Engineer",
    "Data Scientist",
    "DevOps / SRE Engineer",
    "NLP Engineer",
    "Robotics Engineer",
]

PROFILES_PER_JOB = 10  # จำนวน profiles ต่อ job title


def load_job_skills(path: str) -> dict[str, list[dict]]:
    """โหลด required_skills ต่อ job_title จาก labor market dataset"""
    job_skills: dict[str, list[dict]] = collections.defaultdict(list)
    with open(path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            title  = row["job_title"]
            skills = json.loads(row["required_skills"])
            job_skills[title].extend(skills)

    # dedup ต่อ job_title (เก็บ level ที่พบบ่อยที่สุด)
    deduped: dict[str, list[dict]] = {}
    for title, skills in job_skills.items():
        skill_level: dict[str, list[str]] = collections.defaultdict(list)
        for s in skills:
            skill_level[s["name"]].append(s["level"])
        deduped[title] = [
            {"name": name, "level": collections.Counter(levels).most_common(1)[0][0]}
            for name, levels in skill_level.items()
        ]
    return deduped


def get_all_skill_names(job_skills: dict[str, list[dict]]) -> list[str]:
    """รวม skill names ทั้งหมดจากทุก job เพื่อใช้เป็น noise pool"""
    names = set()
    for skills in job_skills.values():
        for s in skills:
            names.add(s["name"])
    return list(names)


def generate_profile(
    job_title: str,
    required_skills: list[dict],
    noise_pool: list[str],
    alumni_id: str,
    coverage: float = 0.70,
    noise_count: int | None = None,
) -> dict:
    """
    สร้าง 1 alumni profile

    coverage   : สัดส่วนของ required skills ที่ใส่เข้าไป (0.6–0.85)
    noise_count: จำนวน skills ที่ไม่เกี่ยวกับ job (0–2)
    """
    # กรอง language skills ออก — ไม่ใช้วัด matching
    tech_skills = [s for s in required_skills if s["name"].lower() not in
                   {"thai", "english", "chinese", "japanese", "korean", "french"}]

    # สุ่มเลือก coverage% ของ tech skills
    k = max(3, int(len(tech_skills) * coverage))
    chosen = random.sample(tech_skills, min(k, len(tech_skills)))

    # สุ่ม level ให้ไม่ match เสมอไป (simulate ความจริง)
    profile_skills = []
    for skill in chosen:
        required_lvl = LEVELS.index(skill["level"]) if skill["level"] in LEVELS else 1
        # 60% โอกาสได้ level ที่ถูก, 30% ต่ำกว่า 1 step, 10% สูงกว่า 1 step
        roll = random.random()
        if roll < 0.60:
            lvl = skill["level"]
        elif roll < 0.90:
            lvl = LEVELS[max(0, required_lvl - 1)]
        else:
            lvl = LEVELS[min(2, required_lvl + 1)]
        profile_skills.append({"name": skill["name"], "level": lvl})

    # เพิ่ม noise skills
    n_noise = noise_count if noise_count is not None else random.randint(0, 2)
    current_names = {s["name"] for s in profile_skills}
    noise_candidates = [n for n in noise_pool if n not in current_names
                        and n.lower() not in {"thai", "english"}]
    noise_skills = random.sample(noise_candidates, min(n_noise, len(noise_candidates)))
    for name in noise_skills:
        profile_skills.append({"name": name, "level": random.choice(LEVELS)})

    random.shuffle(profile_skills)

    return {
        "alumni_id":       alumni_id,
        "first_job_title": job_title,
        "skills":          profile_skills,
        "note":            f"coverage={coverage:.0%}, noise={n_noise}",
    }


def main():
    print("Loading job skills from labor market dataset...")
    job_skills = load_job_skills(LABOR_MARKET_PATH)
    noise_pool = get_all_skill_names(job_skills)

    missing = [j for j in TARGET_JOBS if j not in job_skills]
    if missing:
        print(f"  WARNING: ไม่พบ job titles: {missing}")

    profiles = []
    for job_title in TARGET_JOBS:
        if job_title not in job_skills:
            continue
        required = job_skills[job_title]
        print(f"  Generating {PROFILES_PER_JOB} profiles for: {job_title} ({len(required)} unique skills)")

        for i in range(PROFILES_PER_JOB):
            alumni_id = f"TEST_{job_title.replace(' ', '_').replace('/', '_')}_{i:02d}"
            coverage  = random.uniform(0.60, 0.85)
            profile   = generate_profile(
                job_title    = job_title,
                required_skills = required,
                noise_pool   = noise_pool,
                alumni_id    = alumni_id,
                coverage     = coverage,
            )
            profiles.append(profile)

    # บันทึก CSV
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["alumni_id", "first_job_title", "skills", "note"])
        writer.writeheader()
        for p in profiles:
            writer.writerow({
                "alumni_id":       p["alumni_id"],
                "first_job_title": p["first_job_title"],
                "skills":          json.dumps(p["skills"], ensure_ascii=False),
                "note":            p["note"],
            })

    print(f"\n  Saved {len(profiles)} profiles -> {OUTPUT_PATH}")
    print(f"  Jobs: {len(TARGET_JOBS)}, Profiles per job: {PROFILES_PER_JOB}")
    print(f"  Avg skills per profile: {sum(len(json.loads(p['skills']) if isinstance(p['skills'], str) else p['skills']) for p in profiles) / len(profiles):.1f}")


if __name__ == "__main__":
    main()
