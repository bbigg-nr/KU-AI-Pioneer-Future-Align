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
from predictor import calculate_core_gpa

load_dotenv()

# LangChain imports (lazy-load to avoid slowing startup if not used)
from services.langchain_advisor import LangChainAdvisor
from services.langchain_agent import AgentManager
from routers import ai_advisor as ai_advisor_router


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
            "key_course_grades": json.loads(row.get("key_course_grades", "[]")),
            "target_career":  row["target_career"],
            "activities":     activities_raw,
            "activity_roles": parse_activity_roles(activities_raw),
        }

# โหลด teacher data ไว้ใน memory
TEACHERS: dict[str, dict] = {}
teacher_path = os.getenv("DATA_PATH_TEACHERS", "data/teacher_dataset.csv")
if os.path.exists(teacher_path):
    with open(teacher_path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            TEACHERS[row["teacher_id"]] = {
                "teacher_id":        row["teacher_id"],
                "name":              row["name"],
                "faculty":           row["faculty"],
                "assigned_students": json.loads(row["assigned_students"]),
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

# โหลด skill pool ไว้ใน memory
SKILL_POOL: list[str] = []
job_path = os.getenv("DATA_PATH_JOBS", "data/labor_market_dataset_with_salary.csv")
if os.path.exists(job_path):
    with open(job_path, encoding="utf-8-sig") as f:
        pool = set()
        for row in csv.DictReader(f):
            req_skills = json.loads(row["required_skills"])
            for s in req_skills:
                pool.add(s["name"])
        SKILL_POOL = sorted(list(pool))

# ── Initialize LangChain AI Advisor ──
langchain_advisor = LangChainAdvisor(
    embedding_model=matcher.model,
    chroma_client=matcher.client,
)
agent_manager = AgentManager(
    matcher=matcher,
    advisor=langchain_advisor,
    students_dict=STUDENTS,
)
ai_advisor_router.set_agent_manager(agent_manager)
app.include_router(ai_advisor_router.router)

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

class StudentCreate(BaseModel):
    student_id: str
    name: str
    faculty: str
    year: int
    gpa: float
    target_career: str = ""
    skills: list[SkillItem] = []
    languages: list[SkillItem] = []
    activities: str = ""
    key_course_grades: list[dict] = []

class StudentUpdate(BaseModel):
    name: str | None = None
    faculty: str | None = None
    year: int | None = None
    gpa: float | None = None
    target_career: str | None = None
    skills: list[SkillItem] | None = None
    languages: list[SkillItem] | None = None
    activities: str | None = None



# ---------- Endpoints ----------

@app.get("/")
def root():
    return {"message": "Career Matcher API", "students": len(STUDENTS)}


@app.get("/teachers/{teacher_id}")
def get_teacher(teacher_id: str):
    t = TEACHERS.get(teacher_id)
    if not t:
        raise HTTPException(status_code=404, detail="Teacher not found")
    return t


@app.get("/teachers")
def list_teachers():
    return {"teachers": list(TEACHERS.values()), "total": len(TEACHERS)}


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

@app.get("/skills/pool")
def get_skill_pool():
    """ดึง skill ทั้งหมดในระบบจาก labor market dataset"""
    return {"skills": SKILL_POOL}


@app.post("/students")
def create_student(req: StudentCreate):
    """สร้างโปรไฟล์นิสิตใหม่"""
    if req.student_id in STUDENTS:
        raise HTTPException(status_code=400, detail="Student ID already exists")

    # Add to memory
    new_student = {
        "student_id":     req.student_id,
        "name":           req.name,
        "faculty":        req.faculty,
        "year":           req.year,
        "gpa":            req.gpa,
        "skills":         [s.model_dump() for s in req.skills],
        "languages":      [l.model_dump() for l in req.languages],
        "target_career":  req.target_career,
        "key_course_grades": req.key_course_grades,
        "activities":     req.activities,
        "activity_roles": parse_activity_roles(req.activities),
    }
    STUDENTS[req.student_id] = new_student

    # Append to CSV
    try:
        student_path = os.getenv("DATA_PATH_STUDENTS", "data/synthetic_student_dataset_500_clean.csv")
        file_exists = os.path.isfile(student_path)
        with open(student_path, mode="a", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["student_id","name","faculty","year","gpa","skills","languages","activities","key_course_grades","target_career"])
            
            # Format JSON fields properly for CSV
            skills_json = json.dumps(new_student["skills"], ensure_ascii=False)
            languages_json = json.dumps(new_student["languages"], ensure_ascii=False)
            courses_json = json.dumps(req.key_course_grades, ensure_ascii=False)
            
            writer.writerow([
                req.student_id,
                req.name,
                req.faculty,
                req.year,
                req.gpa,
                skills_json,
                languages_json,
                req.activities,
                courses_json,
                req.target_career
            ])
    except Exception as e:
        # In case CSV appending fails, we still have it in memory, but log error
        print(f"Error appending student to CSV: {e}")
        
    return {"message": "Student created successfully", "student": new_student}


@app.get("/students/{student_id}")
def get_student(student_id: str):
    """ดูข้อมูลนิสิตคนเดียว"""
    s = STUDENTS.get(student_id)
    if not s:
        raise HTTPException(status_code=404, detail="Student not found")
    return {k: v for k, v in s.items() if k != "activity_roles"}

@app.put("/students/{student_id}")
def update_student(student_id: str, req: StudentUpdate):
    """อัปเดตข้อมูลนิสิต"""
    if student_id not in STUDENTS:
        raise HTTPException(status_code=404, detail="Student not found")
        
    s = STUDENTS[student_id]
    
    # Update memory
    if req.name is not None: s["name"] = req.name
    if req.faculty is not None: s["faculty"] = req.faculty
    if req.year is not None: s["year"] = req.year
    if req.gpa is not None: s["gpa"] = req.gpa
    if req.target_career is not None: s["target_career"] = req.target_career
    if req.skills is not None: s["skills"] = [skill.model_dump() for skill in req.skills]
    if req.languages is not None: s["languages"] = [lang.model_dump() for lang in req.languages]
    if req.activities is not None:
        s["activities"] = req.activities
        s["activity_roles"] = parse_activity_roles(req.activities)
        
    # Update CSV safely
    student_path = os.getenv("DATA_PATH_STUDENTS", "data/synthetic_student_dataset_500_clean.csv")
    temp_file = student_path + ".tmp"
    try:
        with open(student_path, mode="r", encoding="utf-8-sig") as infile, \
             open(temp_file, mode="w", encoding="utf-8-sig", newline="") as outfile:
            reader = csv.DictReader(infile)
            writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames)
            writer.writeheader()
            for row in reader:
                if row["student_id"] == student_id:
                    row["name"] = s["name"]
                    row["faculty"] = s["faculty"]
                    row["year"] = str(s["year"])
                    row["gpa"] = str(s["gpa"])
                    row["target_career"] = s["target_career"]
                    row["skills"] = json.dumps(s["skills"], ensure_ascii=False)
                    row["languages"] = json.dumps(s["languages"], ensure_ascii=False)
                    row["activities"] = s["activities"]
                writer.writerow(row)
        os.replace(temp_file, student_path)
    except Exception as e:
        print(f"Error updating student in CSV: {e}")
        
    return {"message": "Student updated successfully", "student": s}

@app.delete("/students/{student_id}")
def delete_student(student_id: str):
    """ลบโปรไฟล์นิสิต"""
    if student_id not in STUDENTS:
        raise HTTPException(status_code=404, detail="Student not found")
        
    del STUDENTS[student_id]
    
    # Update CSV safely
    student_path = os.getenv("DATA_PATH_STUDENTS", "data/synthetic_student_dataset_500_clean.csv")
    temp_file = student_path + ".tmp"
    try:
        with open(student_path, mode="r", encoding="utf-8-sig") as infile, \
             open(temp_file, mode="w", encoding="utf-8-sig", newline="") as outfile:
            reader = csv.DictReader(infile)
            writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames)
            writer.writeheader()
            for row in reader:
                if row["student_id"] != student_id:
                    writer.writerow(row)
        os.replace(temp_file, student_path)
    except Exception as e:
        print(f"Error deleting student in CSV: {e}")
        
    return {"message": "Student deleted successfully"}


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

    combined_skills = s["skills"] + s.get("languages", [])
    result = matcher.match(combined_skills, top_n=req.top_n)

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

    combined_skills = s["skills"] + s.get("languages", [])
    result = matcher.match_archetypes(combined_skills, top_n=req.top_n)
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

    combined_skills = s["skills"] + s.get("languages", [])
    similar = matcher.find_similar_alumni(combined_skills, top_k=req.top_k)
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

    combined_skills = s["skills"] + s.get("languages", [])
    result = matcher.match_blended(
        combined_skills, top_n=req.top_n, alpha=req.alpha, knn_k=req.knn_k,
        activity_roles=s.get("activity_roles", []),
        gpa=s["gpa"],
        core_gpa=calculate_core_gpa(s.get("key_course_grades", [])),
        faculty=s["faculty"],
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
