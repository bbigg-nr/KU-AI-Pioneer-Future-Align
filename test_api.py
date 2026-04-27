"""
test_api.py
-----------
Integration tests สำหรับ Career Matcher API
รัน: pytest test_api.py -v
ต้องรัน server ก่อน: uvicorn main:app --reload --port 8001
"""

import pytest
import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_PORT = os.getenv("API_PORT", "8001")
BASE_URL = f"http://localhost:{API_PORT}"


# ─────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────

@pytest.fixture(scope="session")
def valid_student_id():
    """ดึง student_id จริงจาก /students เพื่อใช้ใน test อื่น"""
    res = requests.get(f"{BASE_URL}/students", params={"limit": 1})
    assert res.status_code == 200
    return res.json()["students"][0]["student_id"]


SKILLS_DATA_SCIENTIST = [
    {"name": "Python",              "level": "Advanced"},
    {"name": "Machine Learning",    "level": "Advanced"},
    {"name": "SQL",                 "level": "Advanced"},
    {"name": "Statistical Modeling","level": "Advanced"},
    {"name": "Pandas / NumPy",      "level": "Advanced"},
    {"name": "Scikit-learn",        "level": "Advanced"},
    {"name": "Data Visualization",  "level": "Intermediate"},
    {"name": "TensorFlow",          "level": "Intermediate"},
    {"name": "Deep Learning",       "level": "Intermediate"},
]

SKILLS_SINGLE = [
    {"name": "Python", "level": "Advanced"},
]

SKILLS_BEGINNER = [
    {"name": "Python",           "level": "Beginner"},
    {"name": "Machine Learning", "level": "Beginner"},
    {"name": "SQL",              "level": "Beginner"},
]

SKILLS_WITH_LANGUAGE = [
    {"name": "Python",   "level": "Advanced"},
    {"name": "Thai",     "level": "Native"},
    {"name": "English",  "level": "Advanced"},
]


# ─────────────────────────────────────────────
# TC01–TC02: Root & Health
# ─────────────────────────────────────────────

class TestHealth:
    def test_tc01_root_returns_200(self):
        """TC01: GET / ต้องคืน 200 พร้อม message และจำนวน students"""
        res = requests.get(f"{BASE_URL}/")
        assert res.status_code == 200
        body = res.json()
        assert "message" in body
        assert "students" in body
        assert isinstance(body["students"], int)
        assert body["students"] > 0

    def test_tc02_health_ok(self):
        """TC02: GET /health ต้อง status=ok และ vectors > 0"""
        res = requests.get(f"{BASE_URL}/health")
        assert res.status_code == 200
        body = res.json()
        assert body["status"] == "ok"
        assert body["vectors"] > 0


# ─────────────────────────────────────────────
# TC03–TC09: Students Endpoints
# ─────────────────────────────────────────────

class TestStudents:
    def test_tc03_list_students_default_limit(self):
        """TC03: GET /students ไม่ส่ง limit → คืน ≤ 20 คน"""
        res = requests.get(f"{BASE_URL}/students")
        assert res.status_code == 200
        body = res.json()
        assert len(body["students"]) <= 20
        assert body["total"] > 0

    def test_tc04_list_students_custom_limit(self):
        """TC04: GET /students?limit=5 → คืนได้ไม่เกิน 5 คน"""
        res = requests.get(f"{BASE_URL}/students", params={"limit": 5})
        assert res.status_code == 200
        assert len(res.json()["students"]) <= 5

    def test_tc05_list_students_schema(self):
        """TC05: แต่ละ student ใน list ต้องมี fields ครบ"""
        res = requests.get(f"{BASE_URL}/students", params={"limit": 3})
        for s in res.json()["students"]:
            assert "student_id"    in s
            assert "name"          in s
            assert "faculty"       in s
            assert "year"          in s
            assert "gpa"           in s
            assert "target_career" in s
            assert "skill_count"   in s
            assert isinstance(s["skill_count"], int)
            assert s["skill_count"] >= 0

    def test_tc06_get_student_valid(self, valid_student_id):
        """TC06: GET /students/{id} ที่มีอยู่จริง → 200 พร้อมข้อมูลครบ"""
        res = requests.get(f"{BASE_URL}/students/{valid_student_id}")
        assert res.status_code == 200
        body = res.json()
        assert body["student_id"] == valid_student_id
        assert "skills"    in body
        assert "languages" in body
        assert isinstance(body["skills"],    list)
        assert isinstance(body["languages"], list)

    def test_tc07_get_student_not_found(self):
        """TC07: GET /students/INVALID → 404"""
        res = requests.get(f"{BASE_URL}/students/INVALID_ID_99999")
        assert res.status_code == 404
        assert "detail" in res.json()

    def test_tc08_student_skills_have_name_and_level(self, valid_student_id):
        """TC08: skills ของนิสิตต้องมี name และ level ทุก item"""
        res = requests.get(f"{BASE_URL}/students/{valid_student_id}")
        for skill in res.json()["skills"]:
            assert "name"  in skill
            assert "level" in skill
            assert skill["level"] in ("Beginner", "Intermediate", "Advanced", "Native")

    def test_tc09_student_gpa_range(self, valid_student_id):
        """TC09: GPA ต้องอยู่ในช่วง 0.0–4.0"""
        res = requests.get(f"{BASE_URL}/students/{valid_student_id}")
        gpa = res.json()["gpa"]
        assert 0.0 <= gpa <= 4.0


# ─────────────────────────────────────────────
# TC10–TC24: POST /match
# ─────────────────────────────────────────────

class TestMatch:
    def test_tc10_normal_match(self):
        """TC10: POST /match กับ skills ปกติ → 200 มี top_jobs"""
        res = requests.post(f"{BASE_URL}/match", json={
            "skills": SKILLS_DATA_SCIENTIST,
            "top_n":  3,
        })
        assert res.status_code == 200
        body = res.json()
        assert "top_jobs" in body
        assert len(body["top_jobs"]) > 0

    def test_tc11_single_skill(self):
        """TC11: ส่ง skill เดียว → ยังคืนผลได้ (ไม่ crash)"""
        res = requests.post(f"{BASE_URL}/match", json={
            "skills": SKILLS_SINGLE,
            "top_n":  3,
        })
        assert res.status_code == 200
        assert "top_jobs" in res.json()

    def test_tc12_top_n_respected(self):
        """TC12: top_n=1 → คืนแค่ 1 job"""
        res = requests.post(f"{BASE_URL}/match", json={
            "skills": SKILLS_DATA_SCIENTIST,
            "top_n":  1,
        })
        assert res.status_code == 200
        assert len(res.json()["top_jobs"]) == 1

    def test_tc13_top_n_large(self):
        """TC13: top_n=10 → คืนไม่เกิน 10 jobs"""
        res = requests.post(f"{BASE_URL}/match", json={
            "skills": SKILLS_DATA_SCIENTIST,
            "top_n":  10,
        })
        assert res.status_code == 200
        assert len(res.json()["top_jobs"]) <= 10

    def test_tc14_empty_skills(self):
        """TC14: skills=[] → top_jobs=[] ไม่ crash"""
        res = requests.post(f"{BASE_URL}/match", json={"skills": []})
        assert res.status_code == 200
        assert res.json()["top_jobs"] == []

    def test_tc15_default_top_n_is_5(self):
        """TC15: ไม่ส่ง top_n → default=5 → คืน ≤ 5 jobs"""
        res = requests.post(f"{BASE_URL}/match", json={"skills": SKILLS_DATA_SCIENTIST})
        assert res.status_code == 200
        assert len(res.json()["top_jobs"]) <= 5

    def test_tc16_missing_skills_field(self):
        """TC16: ไม่ส่ง skills field → 422 Validation Error"""
        res = requests.post(f"{BASE_URL}/match", json={"top_n": 3})
        assert res.status_code == 422

    def test_tc17_invalid_request_body(self):
        """TC17: ส่ง string แทน object → 422"""
        res = requests.post(f"{BASE_URL}/match", json="not a dict")
        assert res.status_code == 422

    def test_tc18_score_range_0_to_1(self):
        """TC18: match_score ทุก job ต้องอยู่ใน [0, 1]"""
        res = requests.post(f"{BASE_URL}/match", json={
            "skills": SKILLS_DATA_SCIENTIST,
            "top_n":  5,
        })
        for job in res.json()["top_jobs"]:
            assert 0.0 <= job["match_score"] <= 1.0, (
                f"{job['job_id']} has score {job['match_score']}"
            )

    def test_tc19_results_sorted_descending(self):
        """TC19: top_jobs เรียงจาก match_score สูงไปต่ำ"""
        res = requests.post(f"{BASE_URL}/match", json={
            "skills": SKILLS_DATA_SCIENTIST,
            "top_n":  5,
        })
        scores = [j["match_score"] for j in res.json()["top_jobs"]]
        assert scores == sorted(scores, reverse=True)

    def test_tc20_total_student_skills_matches_input(self):
        """TC20: total_student_skills ต้องเท่ากับจำนวน skills ที่ส่งไป"""
        res = requests.post(f"{BASE_URL}/match", json={
            "skills": SKILLS_DATA_SCIENTIST,
            "top_n":  3,
        })
        assert res.json()["total_student_skills"] == len(SKILLS_DATA_SCIENTIST)

    def test_tc21_job_schema_complete(self):
        """TC21: แต่ละ job ต้องมี fields ครบ"""
        res = requests.post(f"{BASE_URL}/match", json={
            "skills": SKILLS_DATA_SCIENTIST,
            "top_n":  3,
        })
        for job in res.json()["top_jobs"]:
            assert "job_id"          in job
            assert "job_title"       in job
            assert "match_score"     in job
            assert "matched_skills"  in job
            assert "skills_to_improve" in job
            assert "missing_skills"  in job
            assert isinstance(job["matched_skills"],    list)
            assert isinstance(job["skills_to_improve"], list)
            assert isinstance(job["missing_skills"],    list)

    def test_tc22_advanced_beats_beginner(self):
        """TC22: same skill names, Advanced level → match_score ≥ Beginner สำหรับ job เดียวกัน
        (เปรียบเทียบบน common job_id เพราะ top job ต่างกันได้ตามขนาด job)"""
        shared_names = ["Python", "Machine Learning", "SQL"]
        adv_skills = [{"name": n, "level": "Advanced"} for n in shared_names]
        beg_skills  = [{"name": n, "level": "Beginner"} for n in shared_names]

        adv_jobs = {j["job_id"]: j["match_score"] for j in requests.post(
            f"{BASE_URL}/match", json={"skills": adv_skills, "top_n": 10}
        ).json()["top_jobs"]}

        beg_jobs = {j["job_id"]: j["match_score"] for j in requests.post(
            f"{BASE_URL}/match", json={"skills": beg_skills, "top_n": 10}
        ).json()["top_jobs"]}

        common = set(adv_jobs) & set(beg_jobs)
        assert len(common) > 0, "ไม่พบ common job ให้เปรียบเทียบ"

        for jid in common:
            assert adv_jobs[jid] >= beg_jobs[jid], (
                f"Job {jid}: Advanced={adv_jobs[jid]} < Beginner={beg_jobs[jid]}"
            )

    def test_tc23_language_skills_not_in_match_score(self):
        """TC23: เพิ่ม Thai/English ใน student profile → match_score สำหรับ common jobs ไม่ตก
        (ตรวจว่า language ใน student ไม่ inflate denominator — Option B + code fix)"""
        base_skills = [
            {"name": "Python", "level": "Advanced"},
            {"name": "SQL",    "level": "Advanced"},
        ]
        with_lang = base_skills + [
            {"name": "Thai",    "level": "Native"},
            {"name": "English", "level": "Advanced"},
        ]

        base_jobs = {j["job_id"]: j["match_score"] for j in requests.post(
            f"{BASE_URL}/match", json={"skills": base_skills, "top_n": 10}
        ).json()["top_jobs"]}

        lang_jobs = {j["job_id"]: j["match_score"] for j in requests.post(
            f"{BASE_URL}/match", json={"skills": with_lang, "top_n": 10}
        ).json()["top_jobs"]}

        common = set(base_jobs) & set(lang_jobs)
        assert len(common) > 0, "ไม่พบ common job ให้เปรียบเทียบ"

        for jid in common:
            assert lang_jobs[jid] >= base_jobs[jid] * 0.99, (
                f"Job {jid}: การเพิ่มภาษาทำให้คะแนนลดลง "
                f"({base_jobs[jid]} → {lang_jobs[jid]})"
            )

    def test_tc24_skills_to_improve_level_logic(self):
        """TC24: skills_to_improve ต้องมี your_level ต่ำกว่า need_level เสมอ"""
        res = requests.post(f"{BASE_URL}/match", json={
            "skills": SKILLS_BEGINNER,
            "top_n":  5,
        })
        level_rank = {"Beginner": 1, "Intermediate": 2, "Advanced": 3, "Native": 4}
        for job in res.json()["top_jobs"]:
            for item in job["skills_to_improve"]:
                your  = level_rank.get(item["your_level"],  0)
                need  = level_rank.get(item["need_level"],  0)
                assert your < need, (
                    f"skills_to_improve logic error: {item}"
                )


# ─────────────────────────────────────────────
# TC25–TC30: POST /match/student
# ─────────────────────────────────────────────

class TestMatchStudent:
    def test_tc25_valid_student(self, valid_student_id):
        """TC25: POST /match/student ด้วย student_id ที่มีอยู่ → 200"""
        res = requests.post(f"{BASE_URL}/match/student", json={
            "student_id": valid_student_id,
            "top_n": 3,
        })
        assert res.status_code == 200

    def test_tc26_student_not_found(self):
        """TC26: student_id ไม่มีในระบบ → 404"""
        res = requests.post(f"{BASE_URL}/match/student", json={
            "student_id": "GHOST_999",
            "top_n": 3,
        })
        assert res.status_code == 404

    def test_tc27_response_contains_student_info(self, valid_student_id):
        """TC27: response ต้องมีทั้ง student block และ top_jobs"""
        res = requests.post(f"{BASE_URL}/match/student", json={
            "student_id": valid_student_id,
            "top_n": 3,
        })
        body = res.json()
        assert "student"   in body
        assert "top_jobs"  in body
        assert body["student"]["student_id"] == valid_student_id

    def test_tc28_student_block_schema(self, valid_student_id):
        """TC28: student block ต้องมี fields ครบ"""
        res = requests.post(f"{BASE_URL}/match/student", json={
            "student_id": valid_student_id,
        })
        s = res.json()["student"]
        for field in ("student_id", "name", "faculty", "gpa", "target_career"):
            assert field in s

    def test_tc29_top_n_respected(self, valid_student_id):
        """TC29: top_n=2 ผ่าน /match/student → คืน ≤ 2 jobs"""
        res = requests.post(f"{BASE_URL}/match/student", json={
            "student_id": valid_student_id,
            "top_n": 2,
        })
        assert len(res.json()["top_jobs"]) <= 2

    def test_tc30_student_match_sorted(self, valid_student_id):
        """TC30: top_jobs ใน /match/student เรียงจาก match_score สูงไปต่ำ"""
        res = requests.post(f"{BASE_URL}/match/student", json={
            "student_id": valid_student_id,
            "top_n": 5,
        })
        scores = [j["match_score"] for j in res.json()["top_jobs"]]
        assert scores == sorted(scores, reverse=True)
