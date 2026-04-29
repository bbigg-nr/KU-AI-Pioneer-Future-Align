"""
index_jobs.py
-------------
รันครั้งเดียวเพื่อ encode job skills ทั้งหมดแล้วเก็บลง ChromaDB
รัน: python index_jobs.py
"""

import csv
import json
import os
import chromadb
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

DATA_PATH = os.getenv("DATA_PATH_LABOR", "data/labor_market_dataset_with_salary.csv")
ALUMNI_DATA_PATH = os.getenv("DATA_PATH_ALUMNI", "data/alumni_dataset_500.csv")
CHROMA_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")
COLLECTION_NAME = os.getenv("COLLECTION_JOBS", "job_skills")
ALUMNI_COLLECTION = os.getenv("COLLECTION_ALUMNI", "alumni_profiles")
MODEL_NAME = os.getenv("HF_MODEL_NAME", "paraphrase-multilingual-MiniLM-L12-v2")

LANGUAGE_SKILLS = {
    "thai", "english", "chinese", "japanese", "korean",
    "french", "german", "spanish", "mandarin", "cantonese",
}


def load_jobs(path: str) -> list[dict]:
    jobs = []
    with open(path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            jobs.append({
                "job_id":      row["job_id"],
                "job_title":   row["job_title"],
                "industry":    row["industry"],
                "min_salary":  int(row["min_salary"]) if "min_salary" in row else 0,
                "max_salary":  int(row["max_salary"]) if "max_salary" in row else 0,
                "growth_rate": row.get("growth_rate", ""),
                "required_skills": json.loads(row["required_skills"]),
            })
    return jobs


def load_alumni(path: str) -> list[dict]:
    alumni = []
    with open(path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            alumni.append({
                "alumni_id":          row["alumni_id"],
                "faculty":            row["faculty"],
                "first_job_title":    row["first_job_title"],
                "gpa_at_graduation":  float(row["gpa_at_graduation"]),
                "skills":             json.loads(row["skills_at_graduation"]),
                "key_course_grades":  json.loads(row.get("key_course_grades", "[]")),
                "salary_start":       int(row["salary_start"]),
                "years_to_promotion": int(row["years_to_promotion"]),
                "success_score":      int(row["success_score"]),
            })
    return alumni


def index_alumni(alumni: list[dict], model: SentenceTransformer, client: chromadb.PersistentClient) -> None:
    try:
        client.delete_collection(ALUMNI_COLLECTION)
        print("Deleted existing alumni_profiles collection")
    except Exception:
        pass

    alumni_collection = client.create_collection(
        name=ALUMNI_COLLECTION,
        metadata={"hnsw:space": "cosine"},
    )

    ids, embs, metas = [], [], []

    for alum in alumni:
        tech_skills = [s for s in alum["skills"] if s["name"].lower().strip() not in LANGUAGE_SKILLS]
        if not tech_skills:
            print(f"WARNING: {alum['alumni_id']} has no tech skills — skipped")
            continue

        skill_embs = model.encode([s["name"] for s in tech_skills], batch_size=32)
        mean_emb = skill_embs.mean(axis=0).tolist()

        ids.append(alum["alumni_id"])
        embs.append(mean_emb)
        metas.append({
            "alumni_id":          alum["alumni_id"],
            "faculty":            alum["faculty"],
            "first_job_title":    alum["first_job_title"],
            "gpa_at_graduation":  float(alum["gpa_at_graduation"]),
            "salary_start":       int(alum["salary_start"]),
            "years_to_promotion": int(alum["years_to_promotion"]),
            "success_score":      int(alum["success_score"]),
            "tech_skill_count":   len(tech_skills),
            "tech_skill_names":   json.dumps([s["name"] for s in tech_skills]),
        })

    BATCH = 500
    for i in range(0, len(ids), BATCH):
        alumni_collection.add(
            ids=ids[i:i + BATCH],
            embeddings=embs[i:i + BATCH],
            metadatas=metas[i:i + BATCH],
        )

    print(f"Stored {len(ids)} alumni profiles in {ALUMNI_COLLECTION}")


def index_alumni_rag(alumni: list[dict], model: SentenceTransformer, client: chromadb.PersistentClient) -> None:
    """Index alumni by job title embedding for RAG title-based retrieval.

    แยกออกจาก alumni_profiles (skill-based) เพื่อให้ rag_search ที่รับ job title query
    สามารถ match alumni ที่มี first_job_title ใกล้เคียงได้ถูกต้อง
    โดยไม่กระทบ find_similar_alumni ที่ใช้ skill-based KNN
    """
    RAG_COLLECTION = os.getenv("COLLECTION_ALUMNI_RAG", "alumni_rag_profiles")

    try:
        client.delete_collection(RAG_COLLECTION)
        print(f"Deleted existing {RAG_COLLECTION} collection")
    except Exception:
        pass

    rag_col = client.create_collection(
        name=RAG_COLLECTION,
        metadata={"hnsw:space": "cosine"},
    )

    titles = [alum["first_job_title"] for alum in alumni]
    print(f"Encoding {len(titles)} alumni job title embeddings...")
    title_embs = model.encode(titles, batch_size=64, show_progress_bar=True)

    ids, embs, metas = [], [], []
    for alum, title_emb in zip(alumni, title_embs):
        ids.append(alum["alumni_id"])
        embs.append(title_emb.tolist())
        metas.append({
            "alumni_id":          alum["alumni_id"],
            "faculty":            alum["faculty"],
            "first_job_title":    alum["first_job_title"],
            "gpa_at_graduation":  float(alum["gpa_at_graduation"]),
            "salary_start":       int(alum["salary_start"]),
            "years_to_promotion": int(alum["years_to_promotion"]),
            "success_score":      int(alum["success_score"]),
        })

    BATCH = 500
    for i in range(0, len(ids), BATCH):
        rag_col.add(
            ids=ids[i:i + BATCH],
            embeddings=embs[i:i + BATCH],
            metadatas=metas[i:i + BATCH],
        )

    print(f"Stored {len(ids)} alumni RAG profiles in {RAG_COLLECTION}")


def main():
    print("Loading SBERT model...")
    model = SentenceTransformer(MODEL_NAME)

    print("Loading jobs...")
    jobs = load_jobs(DATA_PATH)
    print(f"  {len(jobs)} jobs loaded")

    # เตรียม ChromaDB
    client = chromadb.PersistentClient(path=CHROMA_PATH)

    # ลบ collection เก่าถ้ามี แล้วสร้างใหม่
    try:
        client.delete_collection(COLLECTION_NAME)
        print("Deleted existing collection")
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},  # ใช้ cosine distance
    )

    # ── Collection 1: per-skill vectors (existing) ──
    all_ids, all_texts, all_meta = [], [], []

    for job in jobs:
        for skill in job["required_skills"]:
            uid = f"{job['job_id']}||{skill['name']}"
            all_ids.append(uid)
            all_texts.append(skill["name"])
            all_meta.append({
                "job_id":      job["job_id"],
                "job_title":   job["job_title"],
                "industry":    job["industry"],
                "min_salary":  job["min_salary"],
                "max_salary":  job["max_salary"],
                "growth_rate": job["growth_rate"],
                "skill_name":  skill["name"],
                "level":       skill["level"],
            })

    print(f"Encoding {len(all_texts)} skill vectors...")
    embeddings = model.encode(all_texts, batch_size=64, show_progress_bar=True)

    BATCH = 500
    for i in range(0, len(all_ids), BATCH):
        collection.add(
            ids=all_ids[i:i+BATCH],
            embeddings=embeddings[i:i+BATCH].tolist(),
            metadatas=all_meta[i:i+BATCH],
        )
        print(f"  Indexed {min(i+BATCH, len(all_ids))}/{len(all_ids)}")

    print(f"\nDone! {len(all_ids)} vectors stored in {COLLECTION_NAME}")

    # ── Collection 2: full-job-summary vectors (NEW — improves RAG faithfulness) ──
    SUMMARY_COLLECTION = os.getenv("COLLECTION_JOB_SUMMARIES", "job_summaries")
    try:
        client.delete_collection(SUMMARY_COLLECTION)
        print(f"Deleted existing {SUMMARY_COLLECTION} collection")
    except Exception:
        pass

    summary_col = client.create_collection(
        name=SUMMARY_COLLECTION,
        metadata={"hnsw:space": "cosine"},
    )

    sum_ids, sum_texts, sum_meta = [], [], []
    for job in jobs:
        skills_text = ", ".join(
            f"{s['name']} ({s['level']})" for s in job["required_skills"]
        )
        summary_text = (
            f"Job: {job['job_title']}. Industry: {job['industry']}. "
            f"Salary: {job['min_salary']}-{job['max_salary']} THB. "
            f"Required skills: {skills_text}."
        )
        sum_ids.append(job["job_id"])
        sum_texts.append(summary_text)
        sum_meta.append({
            "job_id":      job["job_id"],
            "job_title":   job["job_title"],
            "industry":    job["industry"],
            "min_salary":  job["min_salary"],
            "max_salary":  job["max_salary"],
            "growth_rate": job["growth_rate"],
            "skills_text": skills_text,
        })

    print(f"\nEncoding {len(sum_texts)} job summary vectors...")
    sum_embeddings = model.encode(sum_texts, batch_size=64, show_progress_bar=True)

    for i in range(0, len(sum_ids), BATCH):
        summary_col.add(
            ids=sum_ids[i:i+BATCH],
            embeddings=sum_embeddings[i:i+BATCH].tolist(),
            metadatas=sum_meta[i:i+BATCH],
        )
        print(f"  Indexed {min(i+BATCH, len(sum_ids))}/{len(sum_ids)} job summaries")

    print(f"\nDone! {len(sum_ids)} job summaries stored in {SUMMARY_COLLECTION}")

    print("\nIndexing alumni profiles...")
    alumni = load_alumni(ALUMNI_DATA_PATH)
    print(f"  {len(alumni)} alumni loaded")
    index_alumni(alumni, model, client)

    print("\nIndexing alumni RAG profiles (title-based)...")
    index_alumni_rag(alumni, model, client)

    train_predictor(alumni, CHROMA_PATH, MODEL_NAME, client, model)


def train_predictor(
    alumni: list[dict],
    chroma_path: str,
    model_name: str,
    client,
    model,
) -> None:
    from predictor import CareerSuccessPredictor, calculate_core_gpa
    from matcher import SkillMatcher

    print("\nTraining career success predictor...")
    # ส่ง client+model ที่เปิดอยู่แล้วเข้าไป เพื่อหลีกเลี่ยง double ChromaDB client
    matcher = SkillMatcher(
        model_name=model_name,
        chroma_path=chroma_path,
        _client=client,
        _model=model,
    )

    records = []
    for i, alum in enumerate(alumni):
        if not alum["skills"]:
            continue
        result = matcher.match(alum["skills"], top_n=50)
        if not result["top_jobs"]:
            continue

        actual = next(
            (j for j in result["top_jobs"] if j["job_title"] == alum["first_job_title"]),
            result["top_jobs"][0],
        )

        matched_n = len(actual["matched_skills"])
        missing_n = len(actual["missing_skills"])
        total_skills = matched_n + missing_n

        from matcher import LEVEL, _is_language
        tech_levels = [
            LEVEL.get(s.get("level", "Beginner"), 1)
            for s in alum["skills"] if not _is_language(s["name"])
        ]
        avg_skill_level = ((sum(tech_levels) / len(tech_levels)) - 1) / 3 if tech_levels else 0.5

        records.append({
            "match_score":        actual["match_score"],
            "matched_count":      matched_n,
            "missing_count":      missing_n,
            "gpa":                alum["gpa_at_graduation"],
            "core_gpa":           calculate_core_gpa(alum.get("key_course_grades", [])),
            "faculty":            alum["faculty"],
            "success_score":      alum["success_score"],
            "years_to_promotion": alum["years_to_promotion"],
            "coverage_ratio":     matched_n / total_skills if total_skills > 0 else 0.0,
            "avg_skill_level":    avg_skill_level,
        })

        if (i + 1) % 50 == 0:
            print(f"  Processed {i + 1}/{len(alumni)} alumni")

    if not records:
        print("  WARNING: No training records — predictor not saved")
        return

    pred = CareerSuccessPredictor()
    pred.train(records)


if __name__ == "__main__":
    main()
