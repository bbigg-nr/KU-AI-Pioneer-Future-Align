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
        for row in csv.DictReader(f):
            jobs.append({
                "job_id":      row["job_id"],
                "job_title":   row["job_title"],
                "industry":    row["industry"],
                "min_salary":  int(row["min_salary"]),
                "max_salary":  int(row["max_salary"]),
                "growth_rate": row["growth_rate"],
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

    # เตรียม batch
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
    # encode ทั้งหมดใน batch เดียว — เร็วกว่า loop มาก
    embeddings = model.encode(all_texts, batch_size=64, show_progress_bar=True)

    # เพิ่มลง ChromaDB ทีละ 500 (chroma limit)
    BATCH = 500
    for i in range(0, len(all_ids), BATCH):
        collection.add(
            ids=all_ids[i:i+BATCH],
            embeddings=embeddings[i:i+BATCH].tolist(),
            metadatas=all_meta[i:i+BATCH],
        )
        print(f"  Indexed {min(i+BATCH, len(all_ids))}/{len(all_ids)}")

    print(f"\nDone! {len(all_ids)} vectors stored in {CHROMA_PATH}")

    print("\nIndexing alumni profiles...")
    alumni = load_alumni(ALUMNI_DATA_PATH)
    print(f"  {len(alumni)} alumni loaded")
    index_alumni(alumni, model, client)


if __name__ == "__main__":
    main()
