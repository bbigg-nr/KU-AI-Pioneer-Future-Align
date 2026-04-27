"""
matcher.py
----------
Core logic: รับ student skills → query ChromaDB → คืน top-k jobs พร้อม score และ skill gap

Scoring (v2) — ปรับปรุง 3 จุด:
  Option A – coverage-based: หารด้วย matched count ไม่ใช่ total required ทั้งหมด
  Option B – language split: language skills แยกออก ไม่กระทบ domain match_score
  Option C – bidirectional norm: denominator = min(|student_skills|, |tech_required|)
  A + C รวมกัน: match_score = Σ(sim × level_penalty) / min(|student|, |tech_req|)
"""

from __future__ import annotations
import json
import numpy as np
from collections import defaultdict
from sklearn.metrics.pairwise import cosine_similarity
import os
import chromadb
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

# ตั้งค่า HF_TOKEN ให้กับ environment เพื่อให้ library เรียกใช้ได้
if os.getenv("HF_TOKEN"):
    os.environ["HF_TOKEN"] = os.getenv("HF_TOKEN")

LEVEL = {"Beginner": 1, "Intermediate": 2, "Advanced": 3, "Native": 4}

LEVEL_PENALTY = {0: 1.0, 1: 0.6, 2: 0.2, 3: 0.0}

# Option B: ทักษะภาษา — แยกออกจาก domain score, แสดงเป็น info เท่านั้น
LANGUAGE_SKILLS = {
    "thai", "english", "chinese", "japanese", "korean",
    "french", "german", "spanish", "mandarin", "cantonese",
}


def _level_penalty(gap: int) -> float:
    """gap = job_level - student_level (บวก = student ต่ำกว่า)"""
    if gap <= 0:
        return 1.0
    return LEVEL_PENALTY.get(gap, 0.0)


def _is_language(skill_name: str) -> bool:
    return skill_name.lower().strip() in LANGUAGE_SKILLS


class SkillMatcher:
    def __init__(
        self,
        model_name: str = os.getenv("HF_MODEL_NAME", "paraphrase-multilingual-MiniLM-L12-v2"),
        chroma_path: str = os.getenv("CHROMA_DB_PATH", "./chroma_db"),
        collection_name: str = os.getenv("COLLECTION_JOBS", "job_skills"),
        sim_threshold: float = float(os.getenv("SIM_THRESHOLD", 0.75)),
        top_k_candidates: int = int(os.getenv("TOP_K_CANDIDATES", 100)),
    ):
        print("Loading SBERT model...")
        self.model = SentenceTransformer(model_name)
        self.threshold = sim_threshold
        self.top_k = top_k_candidates

        print("Connecting to ChromaDB...")
        self.client = chromadb.PersistentClient(path=chroma_path)
        self.collection = self.client.get_collection(collection_name)
        print(f"  {self.collection.count()} vectors ready")

        try:
            arch_col_name = os.getenv("COLLECTION_ARCHETYPES", "job_archetypes")
            self.archetype_collection = self.client.get_collection(arch_col_name)
            print(f"  {self.archetype_collection.count()} archetypes ready")
        except Exception:
            self.archetype_collection = None
            print("  WARNING: No archetype collection — run index_jobs.py first")

        try:
            alumni_col_name = os.getenv("COLLECTION_ALUMNI", "alumni_profiles")
            self.alumni_collection = self.client.get_collection(alumni_col_name)
            print(f"  {self.alumni_collection.count()} alumni profiles ready")
        except Exception:
            self.alumni_collection = None
            print("  WARNING: No alumni_profiles collection — run index_jobs.py first")

    def match(self, student_skills: list[dict], top_n: int = 5) -> dict:
        """
        Two-Step Matching พร้อม improved scoring (Option A + B + C)

        Formula:
          match_score = Σ(sim × level_penalty for matched tech skills)
                        / min(|student_skills|, |tech_required|)

          - ตัวหารคือ min(...) แทนที่จะเป็น total_required ทั้งหมด
            → ถ้างานต้องการ 12 ทักษะแต่นิสิตมีแค่ 9 → ตัวหาร = 9 (Option C)
            → ถ้างานต้องการ 5 ทักษะและนิสิตมี 9 → ตัวหาร = 5 (Option A)
          - Language skills ไม่นับในตัวหารและตัวตั้ง (Option B)
        """
        if not student_skills:
            return {"top_jobs": [], "total_student_skills": 0}

        # STEP 1: Find Candidate Job IDs (Broad Search)
        skill_names = [s["name"] for s in student_skills]
        s_embeddings = self.model.encode(skill_names, batch_size=32)

        candidate_job_ids = set()
        for emb in s_embeddings:
            res = self.collection.query(query_embeddings=[emb.tolist()], n_results=20)
            for meta in res["metadatas"][0]:
                candidate_job_ids.add(meta["job_id"])

        # STEP 2: Score each Candidate (Exhaustive Match)
        job_results = []
        for job_id in candidate_job_ids:
            job_data = self.collection.get(
                where={"job_id": job_id},
                include=["metadatas", "embeddings"],
            )
            if not job_data["metadatas"]:
                continue

            j_metas = job_data["metadatas"]
            j_embs = job_data["embeddings"]
            job_title = j_metas[0].get("job_title", "Unknown Job")

            # Option B: แยก tech requirements และ language requirements
            tech_items = [(m, e) for m, e in zip(j_metas, j_embs) if not _is_language(m["skill_name"])]
            lang_items  = [(m, e) for m, e in zip(j_metas, j_embs) if _is_language(m["skill_name"])]

            # --- Score tech skills ---
            total_tech_score = 0.0
            matched_skills = []
            skills_to_improve = []
            missing_tech = []

            for j_meta, j_emb in tech_items:
                sims = cosine_similarity([j_emb], s_embeddings)[0]
                best_idx = int(np.argmax(sims))
                best_sim = float(sims[best_idx])
                job_skill_name = j_meta["skill_name"]
                job_skill_level = j_meta["level"]

                if best_sim >= self.threshold:
                    s_skill = student_skills[best_idx]
                    gap = LEVEL.get(job_skill_level, 1) - LEVEL.get(s_skill["level"], 1)
                    penalty = _level_penalty(gap)
                    total_tech_score += best_sim * penalty
                    matched_skills.append(job_skill_name)

                    if gap > 0:
                        skills_to_improve.append({
                            "skill": job_skill_name,
                            "your_level": s_skill["level"],
                            "need_level": job_skill_level,
                        })
                else:
                    missing_tech.append(job_skill_name)

            # Option A + C: denominator = min(|student_tech_skills|, |tech_required|)
            # ใช้ tech skills เท่านั้น (ไม่นับภาษา) เพื่อป้องกัน language ใน student profile
            # ทำให้ denominator โตขึ้นและฉุด tech score โดยไม่ตั้งใจ (ต่อเนื่องจาก Option B)
            student_tech_count = sum(1 for s in student_skills if not _is_language(s["name"]))
            tech_required = len(tech_items)
            denominator = min(student_tech_count, tech_required) if tech_required > 0 else 1
            match_score = total_tech_score / denominator

            # Option B: language skills — informational only, ไม่กระทบ match_score
            missing_lang = []
            for j_meta, j_emb in lang_items:
                sims = cosine_similarity([j_emb], s_embeddings)[0]
                if float(sims.max()) < self.threshold:
                    missing_lang.append(j_meta["skill_name"])

            job_results.append({
                "job_id": job_id,
                "job_title": job_title,
                "match_score": round(match_score, 3),
                "matched_skills": matched_skills,
                "skills_to_improve": skills_to_improve,
                "missing_skills": missing_tech + missing_lang,
            })

        # STEP 3: Sort and Return
        top_jobs = sorted(job_results, key=lambda x: x["match_score"], reverse=True)[:top_n]

        return {
            "top_jobs": top_jobs,
            "total_student_skills": len(student_skills),
        }

    def match_archetypes(self, student_skills: list[dict], top_n: int = 5) -> dict:
        """
        Archetype-based matching:
          1. Query job_archetypes collection with student mean embedding → candidates
          2. Score each archetype using per-skill logic (same as match())
          3. Return top_n archetypes with skill gap + salary info
        """
        if not student_skills or self.archetype_collection is None:
            return {"top_archetypes": [], "total_student_skills": 0}

        skill_names = [s["name"] for s in student_skills]
        s_embeddings = self.model.encode(skill_names, batch_size=32)

        # STEP 1: Multi-query — ค้นหา archetype candidates ด้วยแต่ละ skill แยกกัน
        # แล้ว union เพื่อให้ได้ job_title หลากหลาย (เช่นเดียวกับ match())
        n_per_skill = max(5, top_n * 2)
        candidate_metas: dict[str, dict] = {}  # uid → meta (dedup)
        for emb in s_embeddings:
            res = self.archetype_collection.query(
                query_embeddings=[emb.tolist()],
                n_results=min(n_per_skill, self.archetype_collection.count()),
                include=["metadatas"],
            )
            for meta in res["metadatas"][0]:
                uid = f"{meta['job_title']}||arch_{meta['archetype_id']}"
                candidate_metas[uid] = meta

        # STEP 2: Detailed per-skill scoring against each archetype's skill profile
        archetype_results = []
        for meta in candidate_metas.values():
            skill_profile = json.loads(meta["skill_profile"])
            if not skill_profile:
                continue

            arch_names = [s["name"] for s in skill_profile]
            arch_embs = self.model.encode(arch_names, batch_size=32)

            total_score = 0.0
            matched, to_improve, missing = [], [], []

            for arch_skill, arch_emb in zip(skill_profile, arch_embs):
                sims = cosine_similarity([arch_emb], s_embeddings)[0]
                best_idx = int(np.argmax(sims))
                best_sim = float(sims[best_idx])

                if best_sim >= self.threshold:
                    gap = LEVEL.get(arch_skill["level"], 1) - LEVEL.get(student_skills[best_idx]["level"], 1)
                    penalty = _level_penalty(gap)
                    total_score += best_sim * penalty
                    matched.append(arch_skill["name"])
                    if gap > 0:
                        to_improve.append({
                            "skill": arch_skill["name"],
                            "your_level": student_skills[best_idx]["level"],
                            "need_level": arch_skill["level"],
                        })
                else:
                    missing.append(arch_skill["name"])

            student_tech = sum(1 for s in student_skills if not _is_language(s["name"]))
            tech_req = len(skill_profile)
            denominator = min(student_tech, tech_req) if tech_req > 0 else 1
            match_score = total_score / denominator

            archetype_results.append({
                "job_title":        meta["job_title"],
                "archetype_name":   meta["archetype_name"],
                "match_score":      round(match_score, 3),
                "matched_skills":   matched,
                "skills_to_improve": to_improve,
                "missing_skills":   missing,
                "top_skills":       json.loads(meta["top_skills"]),
                "salary_range":     {"min": meta["avg_min_salary"], "max": meta["avg_max_salary"]},
                "jd_count":         meta["job_count"],
                "industry":         meta["industry"],
            })

        # STEP 3: Dedup by job_title — เก็บ best archetype ต่อตำแหน่ง แล้ว sort
        seen_titles: dict[str, dict] = {}
        for arch in sorted(archetype_results, key=lambda x: x["match_score"], reverse=True):
            title = arch["job_title"]
            if title not in seen_titles:
                seen_titles[title] = arch

        top = list(seen_titles.values())[:top_n]
        return {"top_archetypes": top, "total_student_skills": len(student_skills)}

    def find_similar_alumni(self, student_skills: list[dict], top_k: int = 10) -> list[dict]:
        """KNN on alumni_profiles: คืน top_k alumni ที่ skill profile ใกล้เคียงนิสิตมากที่สุด"""
        if not student_skills or self.alumni_collection is None:
            return []

        tech_skills = [s for s in student_skills if not _is_language(s["name"])]
        if not tech_skills:
            return []

        names = [s["name"] for s in tech_skills]
        s_embs = self.model.encode(names, batch_size=32)
        student_mean_emb = s_embs.mean(axis=0).tolist()

        n_results = min(top_k, self.alumni_collection.count())
        results = self.alumni_collection.query(
            query_embeddings=[student_mean_emb],
            n_results=n_results,
            include=["metadatas", "distances"],
        )

        student_tech_set = {s["name"].lower().strip() for s in tech_skills}
        similar = []
        for meta, dist in zip(results["metadatas"][0], results["distances"][0]):
            alumni_tech_names = json.loads(meta["tech_skill_names"])
            skill_overlap = len(student_tech_set & {n.lower().strip() for n in alumni_tech_names})
            similar.append({
                "alumni_id":          meta["alumni_id"],
                "faculty":            meta["faculty"],
                "first_job_title":    meta["first_job_title"],
                "similarity_score":   round(1.0 - dist, 4),
                "success_score":      meta["success_score"],
                "salary_start":       meta["salary_start"],
                "years_to_promotion": meta["years_to_promotion"],
                "skill_overlap":      skill_overlap,
            })
        return similar

    def rag_search(
        self,
        query: str,
        top_k_jobs: int = 5,
        top_k_alumni: int = 3,
    ) -> dict:
        """
        RAG retrieval: encode user query → ค้น ChromaDB → คืน JDs + alumni ที่เกี่ยวข้อง
        ใช้สำหรับ inject context เข้า AI Advisor ก่อน call Claude
        """
        query_emb = self.model.encode([query])[0].tolist()

        # ── 1. ค้น job_skills ──────────────────────────────────────────────────
        n_job_results = min(top_k_jobs * 5, self.collection.count())
        job_res = self.collection.query(
            query_embeddings=[query_emb],
            n_results=n_job_results,
            include=["metadatas", "distances"],
        )

        # Group skills by job_title → เก็บ best score ต่อ title
        title_map: dict[str, dict] = {}
        for meta, dist in zip(job_res["metadatas"][0], job_res["distances"][0]):
            title = meta["job_title"]
            score = round(1.0 - dist, 4)
            if title not in title_map:
                title_map[title] = {"job_title": title, "relevance": score, "skills": []}
            if score >= title_map[title]["relevance"] * 0.85:  # keep near-best skills
                title_map[title]["skills"].append(
                    f"{meta['skill_name']} ({meta['level']})"
                )

        relevant_jobs = sorted(
            title_map.values(), key=lambda x: x["relevance"], reverse=True
        )[:top_k_jobs]

        # ── 2. ค้น alumni_profiles ─────────────────────────────────────────────
        relevant_alumni = []
        if self.alumni_collection:
            n_alum = min(top_k_alumni, self.alumni_collection.count())
            alum_res = self.alumni_collection.query(
                query_embeddings=[query_emb],
                n_results=n_alum,
                include=["metadatas", "distances"],
            )
            for meta, dist in zip(alum_res["metadatas"][0], alum_res["distances"][0]):
                relevant_alumni.append({
                    "alumni_id":          meta["alumni_id"],
                    "first_job_title":    meta["first_job_title"],
                    "faculty":            meta["faculty"],
                    "salary_start":       meta["salary_start"],
                    "success_score":      meta["success_score"],
                    "years_to_promotion": meta["years_to_promotion"],
                    "similarity":         round(1.0 - dist, 4),
                })

        return {
            "relevant_jobs":   relevant_jobs,
            "relevant_alumni": relevant_alumni,
        }

    def _compute_alumni_career_score(
        self,
        similar_alumni: list[dict],
        candidate_job_titles: set[str],
    ) -> dict[str, float]:
        """คำนวณ alumni-weighted career score ต่อ job_title (normalized ด้วย max weight)"""
        title_weights: dict[str, float] = defaultdict(float)
        for alum in similar_alumni:
            weight = alum["similarity_score"] * (alum["success_score"] / 99.0)
            title_weights[alum["first_job_title"]] += weight

        max_w = max(title_weights.values()) if title_weights else 1.0
        normalized = {title: w / max_w for title, w in title_weights.items()}
        return {title: normalized.get(title, 0.0) for title in candidate_job_titles}

    def match_blended(
        self,
        student_skills: list[dict],
        top_n: int = 5,
        alpha: float = 0.7,
        knn_k: int = 10,
    ) -> dict:
        """
        Blended matching: α × match_score + (1-α) × alumni_career_score

        alumni_career_score มาจาก KNN บน alumni_profiles —
        alumni ที่ skill คล้ายนิสิตและมี success_score สูงจะ contribute มากกว่า
        """
        if self.alumni_collection is None:
            result = self.match(student_skills, top_n=top_n)
            result["alumni_warning"] = "alumni_profiles collection not available; showing match_score only"
            return result

        base_result = self.match(student_skills, top_n=top_n)
        top_jobs = base_result["top_jobs"]

        similar_alumni = self.find_similar_alumni(student_skills, top_k=knn_k)
        candidate_titles = {job["job_title"] for job in top_jobs}
        career_scores = self._compute_alumni_career_score(similar_alumni, candidate_titles)

        blended_jobs = []
        for job in top_jobs:
            title = job["job_title"]
            alumni_cs = career_scores.get(title, 0.0)
            final_score = alpha * job["match_score"] + (1 - alpha) * alumni_cs
            blended_jobs.append({
                **job,
                "alumni_career_score":    round(alumni_cs, 4),
                "final_score":            round(final_score, 4),
                "supporting_alumni_count": sum(
                    1 for a in similar_alumni if a["first_job_title"] == title
                ),
            })

        blended_jobs.sort(key=lambda x: x["final_score"], reverse=True)

        return {
            "top_jobs":             blended_jobs,
            "total_student_skills": base_result["total_student_skills"],
            "alpha":                alpha,
            "knn_k":                knn_k,
            "similar_alumni_count": len(similar_alumni),
        }
