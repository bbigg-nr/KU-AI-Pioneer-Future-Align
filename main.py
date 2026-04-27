"""
main.py
-------
FastAPI web server
รัน: uvicorn main:app --reload --port 8080
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from matcher import SkillMatcher
import csv, json, os, re
from dotenv import load_dotenv

load_dotenv()


def parse_activity_roles(activities_str: str) -> list[str]:
    """ดึง role titles จาก '[Role] at [Org Year]' format"""
    return re.findall(r'\[([^\]]+)\]\s+at\s+\[', activities_str)


app = FastAPI(title="Career Matcher API", version="1.0.0")

# CORS — allow all by default; restrict via CORS_ORIGINS env var in production
cors_origins_raw = os.getenv("CORS_ORIGINS", '["*"]')
cors_origins = json.loads(cors_origins_raw)
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# โหลดครั้งเดียวตอน startup
matcher = SkillMatcher()

# โหลด student data ไว้ใน memory
STUDENTS: dict[str, dict] = {}
student_path = os.getenv("DATA_PATH_STUDENTS", "data/synthetic_student_dataset_500_clean.csv")
with open(student_path, encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        activities_raw = row.get("activities", "")
        STUDENTS[row["student_id"]] = {
            "student_id":     row["student_id"],
            "name":           row["name"],
            "faculty":        row["faculty"],
            "year":           int(row["year"]),
            "gpa":            float(row["gpa"]),
            "skills":         json.loads(row["skills"]),
            "languages":      json.loads(row["languages"]),
            "target_career":  row["target_career"],
            "activities":     activities_raw,
            "activity_roles": parse_activity_roles(activities_raw),
        }

# โหลด alumni data ไว้ใน memory
ALUMNI: dict[str, dict] = {}
alumni_path = os.getenv("DATA_PATH_ALUMNI", "data/alumni_dataset_500.csv")
with open(alumni_path, encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        ALUMNI[row["alumni_id"]] = {
            "alumni_id":          row["alumni_id"],
            "faculty":            row["faculty"],
            "first_job_title":    row["first_job_title"],
            "gpa_at_graduation":  float(row["gpa_at_graduation"]),
            "skills":             json.loads(row["skills_at_graduation"]),
            "salary_start":       int(row["salary_start"]),
            "years_to_promotion": int(row["years_to_promotion"]),
            "success_score":      int(row["success_score"]),
        }


# ---------- Schemas ----------

class SkillItem(BaseModel):
    name: str
    level: str  # Beginner / Intermediate / Advanced / Native

class MatchRequest(BaseModel):
    skills: list[SkillItem]
    top_n: int = 5

class StudentMatchRequest(BaseModel):
    student_id: str
    top_n: int = 5

class AlumniMatchRequest(BaseModel):
    skills: list[SkillItem]
    top_k: int = 10

class StudentAlumniMatchRequest(BaseModel):
    student_id: str
    top_k: int = 10

class BlendedMatchRequest(BaseModel):
    skills: list[SkillItem]
    top_n: int = 5
    alpha: float = 0.7
    knn_k: int = 10

class StudentBlendedMatchRequest(BaseModel):
    student_id: str
    top_n: int = 5
    alpha: float = 0.7
    knn_k: int = 10

class RAGSearchRequest(BaseModel):
    query: str
    top_k_jobs: int = 5
    top_k_alumni: int = 3


# ---------- Endpoints ----------

@app.get("/")
def root():
    return {"message": "Career Matcher API", "students": len(STUDENTS)}


@app.get("/students")
def list_students(limit: int = 20):
    """ดึงรายชื่อนิสิตทั้งหมด"""
    result = []
    for s in list(STUDENTS.values())[:limit]:
        result.append({
            "student_id":   s["student_id"],
            "name":         s["name"],
            "faculty":      s["faculty"],
            "year":         s["year"],
            "gpa":          s["gpa"],
            "target_career": s["target_career"],
            "skill_count":  len(s["skills"]),
        })
    return {"students": result, "total": len(STUDENTS)}


@app.get("/students/{student_id}")
def get_student(student_id: str):
    """ดูข้อมูลนิสิตคนเดียว"""
    s = STUDENTS.get(student_id)
    if not s:
        raise HTTPException(status_code=404, detail="Student not found")
    return {k: v for k, v in s.items() if k != "activity_roles"}


@app.post("/match")
def match_skills(req: MatchRequest):
    """
    Match จาก skills ที่ส่งมาโดยตรง
    ใช้สำหรับ demo หรือ custom input
    """
    skills = [s.model_dump() for s in req.skills]
    result = matcher.match(skills, top_n=req.top_n)
    return result


@app.post("/match/student")
def match_student(req: StudentMatchRequest):
    """
    Match จาก student_id
    ดึง skills ของนิสิตจาก DB แล้ว match
    """
    s = STUDENTS.get(req.student_id)
    if not s:
        raise HTTPException(status_code=404, detail="Student not found")

    result = matcher.match(s["skills"], top_n=req.top_n)

    return {
        "student": {
            "student_id":   s["student_id"],
            "name":         s["name"],
            "faculty":      s["faculty"],
            "gpa":          s["gpa"],
            "target_career": s["target_career"],
        },
        **result,
    }


@app.post("/match/archetype")
def match_archetype(req: MatchRequest):
    """
    Match จาก skills ที่ส่งมา แล้วคืน job archetypes แทน individual JDs
    แต่ละ archetype คือ cluster ของ JD ที่ต้องการ skill set คล้ายกัน
    """
    skills = [s.model_dump() for s in req.skills]
    return matcher.match_archetypes(skills, top_n=req.top_n)


@app.post("/match/student/archetype")
def match_student_archetype(req: StudentMatchRequest):
    """Match จาก student_id แล้วคืน job archetypes"""
    s = STUDENTS.get(req.student_id)
    if not s:
        raise HTTPException(status_code=404, detail="Student not found")

    result = matcher.match_archetypes(s["skills"], top_n=req.top_n)
    return {
        "student": {
            "student_id":    s["student_id"],
            "name":          s["name"],
            "faculty":       s["faculty"],
            "gpa":           s["gpa"],
            "target_career": s["target_career"],
        },
        **result,
    }


@app.post("/match/alumni")
def match_alumni(req: AlumniMatchRequest):
    """หา alumni ที่ skill ใกล้เคียงที่สุด (KNN) จาก skills ที่ส่งมา"""
    skills = [s.model_dump() for s in req.skills]
    similar = matcher.find_similar_alumni(skills, top_k=req.top_k)
    return {
        "similar_alumni":   similar,
        "total_found":      len(similar),
        "query_skill_count": len(skills),
    }


@app.post("/match/student/alumni")
def match_student_alumni(req: StudentAlumniMatchRequest):
    """หา alumni ที่ skill ใกล้เคียงที่สุด (KNN) จาก student_id"""
    s = STUDENTS.get(req.student_id)
    if not s:
        raise HTTPException(status_code=404, detail="Student not found")

    similar = matcher.find_similar_alumni(s["skills"], top_k=req.top_k)
    return {
        "student": {
            "student_id":    s["student_id"],
            "name":          s["name"],
            "faculty":       s["faculty"],
            "gpa":           s["gpa"],
            "target_career": s["target_career"],
        },
        "similar_alumni": similar,
        "total_found":    len(similar),
    }


@app.post("/match/blended")
def match_blended(req: BlendedMatchRequest):
    """Blended job match: α × skill_match + (1-α) × alumni_career_signal"""
    skills = [s.model_dump() for s in req.skills]
    return matcher.match_blended(
        skills, top_n=req.top_n, alpha=req.alpha, knn_k=req.knn_k
    )


@app.post("/match/student/blended")
def match_student_blended(req: StudentBlendedMatchRequest):
    """Blended job match จาก student_id"""
    s = STUDENTS.get(req.student_id)
    if not s:
        raise HTTPException(status_code=404, detail="Student not found")

    result = matcher.match_blended(
        s["skills"], top_n=req.top_n, alpha=req.alpha, knn_k=req.knn_k,
        activity_roles=s.get("activity_roles", []),
    )
    return {
        "student": {
            "student_id":    s["student_id"],
            "name":          s["name"],
            "faculty":       s["faculty"],
            "gpa":           s["gpa"],
            "target_career": s["target_career"],
        },
        **result,
    }


@app.post("/rag/search")
def rag_search(req: RAGSearchRequest):
    """
    RAG retrieval endpoint — ใช้โดย AI Advisor ก่อน call Claude
    รับ query text → คืน relevant JDs + alumni จาก ChromaDB
    """
    return matcher.rag_search(
        query=req.query,
        top_k_jobs=req.top_k_jobs,
        top_k_alumni=req.top_k_alumni,
    )


@app.get("/health")
def health():
    arch_count   = matcher.archetype_collection.count() if matcher.archetype_collection else 0
    alumni_count = matcher.alumni_collection.count() if matcher.alumni_collection else 0
    return {
        "status":          "ok",
        "vectors":         matcher.collection.count(),
        "archetypes":      arch_count,
        "alumni_profiles": alumni_count,
    }
