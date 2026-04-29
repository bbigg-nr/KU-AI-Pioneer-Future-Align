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
from predictor import CareerSuccessPredictor

load_dotenv()

# ตั้งค่า HF_TOKEN ให้กับ environment เพื่อให้ library เรียกใช้ได้
if os.getenv("HF_TOKEN"):
    os.environ["HF_TOKEN"] = os.getenv("HF_TOKEN")

LEVEL = {"Beginner": 1, "Intermediate": 2, "Advanced": 3, "Native": 4}

# Core skills extracted from CAREER_SKILL_MAP in Generate_DATA.py — get 1.5× weight
CORE_SKILLS: frozenset[str] = frozenset({
    'A/B Testing', 'AWS (EC2, S3, Lambda)', 'Academic Paper Writing',
    'Agile / Scrum Methodology', 'Airflow', 'Ansible', 'Apache Kafka', 'Apache Spark',
    'Assembly Language', 'Attention to Detail', 'Azure (AKS, Functions)',
    'Bash/Shell Scripting', 'Behavioral Finance', 'Bloomberg Terminal',
    'C#', 'C++', 'C/C++', 'CI/CD Pipelines', 'Capital Budgeting',
    'Causal Inference (DiD, RDD, IV)', 'Communication', 'Computer Graphics',
    'Computer System Security', 'Computer Vision', 'Convolutional Neural Networks',
    'Corporate Finance', 'Cost-Benefit Analysis (CBA)', 'Credit Analysis',
    'Cryptography', 'Data Analytics', 'Data Engineering', 'Data Structures & Algorithms',
    'Data Visualization', 'Deep Learning', 'Derivatives Pricing (Black-Scholes)',
    'Digital Game Production', 'Digital Image Processing', 'Digital Systems Design',
    'Django', 'Docker', 'Economic Forecasting', 'Econometrics', 'Elasticsearch',
    'Embedded Systems (Arduino/Raspberry Pi)', 'Embedded System (Course)',
    'Environmental Economics', 'Equity Research', 'Excel (Advanced: Solver, VBA, Power Query)',
    'Express.js', 'FPGA Programming', 'Factor Investing', 'FastAPI',
    'Feature Engineering', 'Figma (UI/UX)', 'Financial Economics', 'Financial Modeling',
    'Financial Statement Analysis', 'Fixed Income Analysis', 'Flask',
    'GCP (BigQuery, GKE)', 'Git / Version Control', 'GitHub Actions', 'Go',
    'Hadoop', 'Hugging Face Transformers', 'Industry Analysis', 'Investment Analysis',
    'Investment Banking (M&A Modeling)', 'IoT Development', 'JIRA / Agile Tools',
    'Java', 'JavaScript', 'Julia (Economic Modeling)', 'Jupyter Notebook',
    'Keras', 'Kubernetes', 'LLM Fine-tuning', 'LangChain', 'Leadership',
    'Linux System Admin', 'MATLAB (Economic Modeling)', 'Machine Learning',
    'Macro Modeling (DSGE, CGE)', 'Microcontroller Programming',
    'Microservices Architecture', 'Model Deployment (MLOps)', 'Monte Carlo Simulation',
    'National Accounts Analysis', 'Natural Language Processing', 'Negotiation',
    'Network Security', 'Next.js', 'Nginx', 'Node.js',
    'OWASP Top 10', 'Object-Oriented Design', 'OpenCV',
    'Pandas / NumPy', 'Parallel and Distributed Computing Systems',
    'Penetration Testing', 'Physics Engine Programming', 'Policy Brief Writing',
    'Portfolio Management', 'PostgreSQL', 'Power BI', 'Presentation Skills',
    'Product Roadmapping', 'Prometheus & Grafana', 'Prompt Engineering',
    'PyTorch', 'Python', 'Python (Pandas, NumPy, Statsmodels)',
    'Quantitative Trading', 'R (ggplot2, dplyr, tidyr)', 'RAG (Retrieval-Augmented Generation)',
    'REST API Design', 'Real-Time Operating Systems (RTOS)', 'Redis',
    'Regression Analysis', 'Report Writing', 'Research Design', 'Research Methods in Economics',
    'Reuters Eikon', 'Risk Management (VaR, CVaR)', 'SIEM Tools',
    'SQL', 'SQL (Data Querying)', 'Scikit-learn', 'Social Impact Evaluation',
    'Software Engineering', 'Spring Boot', 'Stakeholder Management',
    'Stata', 'Statistical Modeling', 'Stochastic Modeling',
    'Sustainability Reporting', 'TCP/IP Networking', 'Tableau', 'TensorFlow',
    'Terraform', 'Time Series Forecasting', 'TypeScript',
    'Unity / Unreal Engine', 'Unit Testing', 'User Research',
    'Valuation (DCF, Comps)', 'Vector Databases (Pinecone/Weaviate)',
    'Vue.js', 'Vulnerability Assessment', 'dbt (Data Build Tool)',
    'Economics Statistics I/II', 'Economics of Financial Risk Management',
    'Economics of Money and Banking', 'Economics of Natural Resources and Public Policy',
    'Financial Economics',
})

# Option B: ทักษะภาษา — แยกออกจาก domain score, แสดงเป็น info เท่านั้น
LANGUAGE_SKILLS = {
    "thai", "english", "chinese", "japanese", "korean",
    "french", "german", "spanish", "mandarin", "cantonese",
}


def _level_penalty(gap: int) -> float:
    """gap = job_level - student_level (บวก = student ต่ำกว่า)
    Smooth exponential decay แทน step function:
      gap=0 → 1.0, gap=1 → 0.65, gap=2 → 0.35, gap=3 → 0.15, gap≥4 → ~0.0
    """
    if gap <= 0:
        return 1.0
    return round(float(np.exp(-0.5 * gap)), 4)


def _is_language(skill_name: str) -> bool:
    return skill_name.lower().strip() in LANGUAGE_SKILLS


class SkillMatcher:
    def __init__(
        self,
        model_name: str = os.getenv("HF_MODEL_NAME", "paraphrase-multilingual-MiniLM-L12-v2"),
        chroma_path: str = os.getenv("CHROMA_DB_PATH", "./chroma_db"),
        collection_name: str = os.getenv("COLLECTION_JOBS", "job_skills"),
        sim_threshold: float = float(os.getenv("SIM_THRESHOLD", 0.85)),
        top_k_candidates: int = int(os.getenv("TOP_K_CANDIDATES", 100)),
        _client: chromadb.PersistentClient | None = None,
        _model: SentenceTransformer | None = None,
    ):
        if _model is not None:
            self.model = _model
        else:
            print("Loading SBERT model...")
            self.model = SentenceTransformer(model_name)
        self.threshold = sim_threshold
        self.top_k = top_k_candidates

        if _client is not None:
            self.client = _client
        else:
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

        try:
            rag_alumni_col_name = os.getenv("COLLECTION_ALUMNI_RAG", "alumni_rag_profiles")
            self.alumni_rag_collection = self.client.get_collection(rag_alumni_col_name)
            print(f"  {self.alumni_rag_collection.count()} alumni RAG profiles ready")
        except Exception:
            self.alumni_rag_collection = None
            print("  INFO: No alumni_rag_profiles — run index_jobs.py to enable title-based RAG")

        try:
            summary_col_name = os.getenv("COLLECTION_JOB_SUMMARIES", "job_summaries")
            self.job_summary_collection = self.client.get_collection(summary_col_name)
            print(f"  {self.job_summary_collection.count()} job summaries ready")
        except Exception:
            self.job_summary_collection = None
            print("  INFO: No job_summaries — run index_jobs.py to enable full-context RAG")

        self.predictor = CareerSuccessPredictor.load()
        if self.predictor.is_fitted:
            print("  Career success predictor loaded")
        else:
            print("  WARNING: No predictor model — run index_jobs.py first")

    def match(self, student_skills: list[dict], top_n: int = 5, s_embeddings: np.ndarray | None = None) -> dict:
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
        if s_embeddings is None:
            s_embeddings = self.model.encode(skill_names, batch_size=32)

        candidate_job_ids = set()
        res = self.collection.query(query_embeddings=s_embeddings.tolist(), n_results=20)
        for metas in res["metadatas"]:
            for meta in metas:
                candidate_job_ids.add(meta["job_id"])

        # STEP 2: Score each Candidate (Exhaustive Match)
        job_results = []
        if not candidate_job_ids:
            return {"top_jobs": [], "total_student_skills": len(student_skills)}

        # Batch GET to avoid N queries to ChromaDB (huge performance gain)
        job_data_all = self.collection.get(
            where={"job_id": {"$in": list(candidate_job_ids)}},
            include=["metadatas", "embeddings"],
        )
        job_dict = defaultdict(lambda: {"metadatas": [], "embeddings": []})
        if job_data_all and job_data_all["metadatas"]:
            for meta, emb in zip(job_data_all["metadatas"], job_data_all["embeddings"]):
                job_id = meta["job_id"]
                job_dict[job_id]["metadatas"].append(meta)
                job_dict[job_id]["embeddings"].append(emb)

        for job_id, job_data in job_dict.items():
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
            weighted_denominator = 0.0
            matched_skills = []
            skills_to_improve = []
            missing_tech = []

            # Soft threshold: sim < SOFT_LOW → 0, sim = threshold → 1.0, sim > threshold → bonus
            SOFT_LOW = 0.5
            CORE_WEIGHT = 1.5   # core skills count more; adjacent skills = 1.0

            if tech_items:
                j_embs_tech = np.array([e for m, e in tech_items])
                sims_matrix = cosine_similarity(j_embs_tech, s_embeddings)

                for i, (j_meta, _) in enumerate(tech_items):
                    sims = sims_matrix[i]
                    best_idx = int(np.argmax(sims))
                    best_sim = float(sims[best_idx])
                    job_skill_name = j_meta["skill_name"]
                    job_skill_level = j_meta["level"]
                    skill_weight = CORE_WEIGHT if job_skill_name in CORE_SKILLS else 1.0

                    s_skill = student_skills[best_idx]
                    gap = LEVEL.get(job_skill_level, 1) - LEVEL.get(s_skill["level"], 1)

                    contribution = max(0.0, (best_sim - SOFT_LOW) / (self.threshold - SOFT_LOW))
                    if contribution > 0:
                        penalty = _level_penalty(gap)
                        total_tech_score += contribution * penalty * skill_weight

                    weighted_denominator += skill_weight

                    if best_sim >= self.threshold:
                        matched_skills.append(job_skill_name)
                        if gap > 0:
                            skills_to_improve.append({
                                "skill": job_skill_name,
                                "your_level": s_skill["level"],
                                "need_level": job_skill_level,
                            })
                    else:
                        missing_tech.append(job_skill_name)

            # Denominator: min(student weighted capacity, job weighted demand)
            student_tech_count = sum(1 for s in student_skills if not _is_language(s["name"]))
            tech_required = len(tech_items)
            # student capacity in weighted units (assume uniform weight 1.0 — conservative)
            student_weighted = float(student_tech_count)
            denom = min(student_weighted, weighted_denominator) if tech_required > 0 else 1.0
            raw_score = min(total_tech_score / denom, 1.0) if denom > 0 else 0.0
            # Coverage penalty: prevent full score when student only covers a fraction of required skills
            # e.g. 3/10 required → coverage=0.3 → multiplier=0.79 ; 10/10 → multiplier=1.0
            coverage = len(matched_skills) / tech_required if tech_required > 0 else 1.0
            match_score = raw_score * (0.7 + 0.3 * coverage)

            # Option B: language skills — informational only, ไม่กระทบ match_score
            missing_lang = []
            if lang_items:
                j_embs_lang = np.array([e for m, e in lang_items])
                sims_matrix_lang = cosine_similarity(j_embs_lang, s_embeddings)
                for i, (j_meta, _) in enumerate(lang_items):
                    if float(sims_matrix_lang[i].max()) < self.threshold:
                        missing_lang.append(j_meta["skill_name"])

            job_results.append({
                "job_id": job_id,
                "job_title": job_title,
                "match_score": round(match_score, 3),
                "matched_skills": matched_skills,
                "skills_to_improve": skills_to_improve,
                "missing_skills": missing_tech + missing_lang,
            })

        # STEP 3: Dedup by job_title (keep best score per title) → Sort → Return
        # หลาย JD อาจมี job_title เดียวกัน (เช่น "Backend Engineer" 2 บริษัท)
        # dedup ก่อนเพื่อให้ top_n คือ top_n ตำแหน่งที่แตกต่างกัน
        seen_titles: dict[str, dict] = {}
        for job in sorted(job_results, key=lambda x: x["match_score"], reverse=True):
            if job["job_title"] not in seen_titles:
                seen_titles[job["job_title"]] = job

        top_jobs = list(seen_titles.values())[:top_n]

        return {
            "top_jobs": top_jobs,
            "total_student_skills": len(student_skills),
        }

    def match_archetypes(self, student_skills: list[dict], top_n: int = 5, s_embeddings: np.ndarray | None = None) -> dict:
        """
        Archetype-based matching:
          1. Query job_archetypes collection with student mean embedding → candidates
          2. Score each archetype using per-skill logic (same as match())
          3. Return top_n archetypes with skill gap + salary info
        """
        if not student_skills or self.archetype_collection is None:
            return {"top_archetypes": [], "total_student_skills": 0}

        skill_names = [s["name"] for s in student_skills]
        if s_embeddings is None:
            s_embeddings = self.model.encode(skill_names, batch_size=32)

        # STEP 1: Multi-query — ค้นหา archetype candidates ด้วยแต่ละ skill แยกกัน
        # แล้ว union เพื่อให้ได้ job_title หลากหลาย (เช่นเดียวกับ match())
        n_per_skill = max(5, top_n * 2)
        candidate_metas: dict[str, dict] = {}  # uid → meta (dedup)
        
        res = self.archetype_collection.query(
            query_embeddings=s_embeddings.tolist(),
            n_results=min(n_per_skill, self.archetype_collection.count()),
            include=["metadatas"],
        )
        for metas in res["metadatas"]:
            for meta in metas:
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

            if len(arch_embs) > 0:
                sims_matrix = cosine_similarity(arch_embs, s_embeddings)

                for i, arch_skill in enumerate(skill_profile):
                    sims = sims_matrix[i]
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

    def find_similar_alumni(self, student_skills: list[dict], top_k: int = 10, s_embeddings: np.ndarray | None = None) -> list[dict]:
        """KNN on alumni_profiles: คืน top_k alumni ที่ skill profile ใกล้เคียงนิสิตมากที่สุด"""
        if not student_skills or self.alumni_collection is None:
            return []

        tech_indices = [i for i, s in enumerate(student_skills) if not _is_language(s["name"])]
        if not tech_indices:
            return []
        
        tech_skills = [student_skills[i] for i in tech_indices]

        if s_embeddings is not None:
            s_embs = s_embeddings[tech_indices]
        else:
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
        sim_threshold: float = 0.50,
    ) -> dict:
        """
        RAG retrieval: encode user query → ค้น ChromaDB → คืน JDs + alumni ที่เกี่ยวข้อง
        ใช้สำหรับ inject context เข้า AI Advisor ก่อน call Claude

        Job search ใช้ multi-query (แต่ละ term แยกกัน) เพื่อให้ relevance score สูงขึ้น
        เทียบกับ blended multi-keyword embedding เดียว

        *** IMPROVED v2 ***
        - ถ้ามี job_summaries collection → ใช้เป็นหลัก (context ครบ: title + industry + skills + salary)
          ช่วยให้ LLM ตอบได้ grounded มากขึ้น → เพิ่ม Faithfulness
        - กรองผลลัพธ์ด้วย sim_threshold เพื่อลบ noise ออกจาก context ที่ส่งให้ LLM
        """
        # ── 1. Job retrieval ──────────────────────────────────────────────────
        query_emb = self.model.encode([query])[0].tolist()
        relevant_jobs: list[dict] = []

        # Strategy A: ใช้ job_summaries ถ้ามี (full-context per job)
        if self.job_summary_collection is not None:
            n_results = min(top_k_jobs * 2, self.job_summary_collection.count())
            sum_res = self.job_summary_collection.query(
                query_embeddings=[query_emb],
                n_results=n_results,
                include=["metadatas", "distances"],
            )
            for meta, dist in zip(sum_res["metadatas"][0], sum_res["distances"][0]):
                score = round(1.0 - dist, 4)
                if score < sim_threshold:
                    continue
                relevant_jobs.append({
                    "job_title":   meta["job_title"],
                    "relevance":   score,
                    "skills":      meta.get("skills_text", "").split(", ") if meta.get("skills_text") else [],
                    "industry":    meta.get("industry", ""),
                    "min_salary":  meta.get("min_salary", 0),
                    "max_salary":  meta.get("max_salary", 0),
                })
            relevant_jobs = relevant_jobs[:top_k_jobs]

        # Strategy B: fallback ไป job_skills (per-skill) ถ้า job_summaries ไม่มี หรือไม่พอ
        if not relevant_jobs:
            terms = [t.strip() for t in query.split() if len(t.strip()) > 2][:12]
            if not terms:
                terms = [query]

            term_embs = self.model.encode(terms, batch_size=32)
            title_map: dict[str, dict] = {}
            title_skills_seen: dict[str, set] = {}
            n_per_term = min(top_k_jobs * 6, self.collection.count())

            res = self.collection.query(
                query_embeddings=term_embs.tolist(),
                n_results=n_per_term,
                include=["metadatas", "distances"],
            )
            for metas, dists in zip(res["metadatas"], res["distances"]):
                for meta, dist in zip(metas, dists):
                    title = meta["job_title"]
                    score = round(1.0 - dist, 4)
                    if score < sim_threshold:
                        continue
                    if title not in title_map:
                        title_map[title] = {"job_title": title, "relevance": score, "skills": []}
                        title_skills_seen[title] = set()
                    elif score > title_map[title]["relevance"]:
                        title_map[title]["relevance"] = score

                    skill_key = meta["skill_name"]
                    if skill_key not in title_skills_seen[title]:
                        title_map[title]["skills"].append(
                            f"{meta['skill_name']} ({meta['level']})"
                        )
                        title_skills_seen[title].add(skill_key)

            relevant_jobs = sorted(
                title_map.values(), key=lambda x: x["relevance"], reverse=True
            )[:top_k_jobs]

        # ── 2. Alumni retrieval ────────────────────────────────────────────────
        relevant_alumni = []
        alumni_col = self.alumni_rag_collection if self.alumni_rag_collection is not None else self.alumni_collection
        if alumni_col is not None:
            n_alum = min(top_k_alumni * 2, alumni_col.count())
            alum_res = alumni_col.query(
                query_embeddings=[query_emb],
                n_results=n_alum,
                include=["metadatas", "distances"],
            )
            for meta, dist in zip(alum_res["metadatas"][0], alum_res["distances"][0]):
                sim = round(1.0 - dist, 4)
                if sim < sim_threshold:
                    continue
                relevant_alumni.append({
                    "alumni_id":          meta["alumni_id"],
                    "first_job_title":    meta["first_job_title"],
                    "faculty":            meta["faculty"],
                    "salary_start":       meta["salary_start"],
                    "success_score":      meta["success_score"],
                    "years_to_promotion": meta["years_to_promotion"],
                    "similarity":         sim,
                })
            relevant_alumni = relevant_alumni[:top_k_alumni]

        return {
            "relevant_jobs":   relevant_jobs,
            "relevant_alumni": relevant_alumni,
        }

    def _compute_alumni_career_score(
        self,
        similar_alumni: list[dict],
        candidate_job_titles: set[str],
        activity_roles: list[str] | None = None,
    ) -> dict[str, float]:
        """คำนวณ alumni-weighted career score ต่อ job_title (normalized ด้วย max weight)

        ถ้า alumni's first_job_title คล้ายกับ activity roles ของนิสิต → weight × activity_boost
        """
        act_embs = None
        if activity_roles:
            act_embs = self.model.encode(activity_roles, batch_size=32)

        title_weights: dict[str, float] = defaultdict(float)
        
        alum_job_titles = [alum["first_job_title"] for alum in similar_alumni]
        sims_matrix = None
        if act_embs is not None and alum_job_titles:
            alum_job_embs = self.model.encode(alum_job_titles, batch_size=32)
            sims_matrix = cosine_similarity(alum_job_embs, act_embs)

        for i, alum in enumerate(similar_alumni):
            weight = alum["similarity_score"] * (alum["success_score"] / 99.0)

            if sims_matrix is not None:
                activity_sim = float(sims_matrix[i].max())
                # Continuous boost: 0.5→1.0x, 0.75→1.25x, 1.0→1.5x (no hard cliff at 0.65)
                boost = 1.0 + 0.5 * max(0.0, (activity_sim - 0.5) / 0.5)
                weight *= boost

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
        activity_roles: list[str] | None = None,
        gpa: float = 3.0,
        core_gpa: float = 0.0,
        faculty: str = "Unknown",
    ) -> dict:
        """
        Blended matching:
          α × match_score
          + (1-α) × 0.7 × alumni_career_score
          + (1-α) × 0.3 × predicted_success   ← Predictive Analytics

        alumni_career_score มาจาก KNN บน alumni_profiles
        predicted_success มาจาก GradientBoosting ที่ train จาก alumni outcome data
        """
        if not student_skills:
            return {"top_jobs": [], "total_student_skills": 0, "alpha": alpha, "knn_k": knn_k, "similar_alumni_count": 0, "predictor_active": False, "predictor_training_size": 0}

        skill_names = [s["name"] for s in student_skills]
        s_embeddings = self.model.encode(skill_names, batch_size=32)

        if self.alumni_collection is None:
            result = self.match(student_skills, top_n=top_n, s_embeddings=s_embeddings)
            result["alumni_warning"] = "alumni_profiles collection not available; showing match_score only"
            return result

        base_result = self.match(student_skills, top_n=top_n, s_embeddings=s_embeddings)
        top_jobs = base_result["top_jobs"]

        similar_alumni = self.find_similar_alumni(student_skills, top_k=knn_k, s_embeddings=s_embeddings)
        candidate_titles = {job["job_title"] for job in top_jobs}
        career_scores = self._compute_alumni_career_score(similar_alumni, candidate_titles, activity_roles=activity_roles)

        # 4.1 Dynamic alpha: trust skill match more when predictor has little training data
        training_size = self.predictor.training_size
        if not self.predictor.is_fitted:
            effective_alpha = 1.0
        elif training_size > 100:
            effective_alpha = alpha          # caller default (0.7)
        else:
            effective_alpha = 0.85           # small dataset → lean on skill match

        # Precompute avg_skill_level from student profile (normalized LEVEL 1-4 → 0-1)
        tech_levels = [
            LEVEL.get(s.get("level", "Beginner"), 1)
            for s in student_skills if not _is_language(s["name"])
        ]
        avg_skill_level = ((sum(tech_levels) / len(tech_levels)) - 1) / 3 if tech_levels else 0.5

        blended_jobs = []
        for job in top_jobs:
            title = job["job_title"]
            alumni_cs = career_scores.get(title, 0.0)

            matched_n = len(job["matched_skills"])
            missing_n = len(job["missing_skills"])
            coverage_ratio = matched_n / (matched_n + missing_n) if (matched_n + missing_n) > 0 else 0.0

            predicted = self.predictor.predict(
                match_score=job["match_score"],
                matched_count=matched_n,
                missing_count=missing_n,
                gpa=gpa,
                core_gpa=core_gpa,
                faculty=faculty,
                coverage_ratio=coverage_ratio,
                avg_skill_level=avg_skill_level,
            )

            remainder = 1 - effective_alpha
            if alumni_cs > 0:
                final_score = (
                    effective_alpha * job["match_score"]
                    + remainder * 0.7 * alumni_cs
                    + remainder * 0.3 * predicted
                )
            else:
                final_score = effective_alpha * job["match_score"] + remainder * predicted
            blended_jobs.append({
                **job,
                "alumni_career_score":     round(alumni_cs, 4),
                "predicted_success":       round(predicted, 4),
                "final_score":             round(final_score, 4),
                "supporting_alumni_count": sum(
                    1 for a in similar_alumni if a["first_job_title"] == title
                ),
            })

        blended_jobs.sort(key=lambda x: x["final_score"], reverse=True)

        return {
            "top_jobs":             blended_jobs,
            "total_student_skills": base_result["total_student_skills"],
            "alpha":                effective_alpha,
            "knn_k":                knn_k,
            "similar_alumni_count": len(similar_alumni),
            "predictor_active":     self.predictor.is_fitted,
            "predictor_training_size": training_size,
        }
