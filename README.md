# Career Matcher — Setup Guide

## โครงสร้าง Project

```
career-matcher/
├── data/
│   ├── labor_market_dataset_with_salary.csv
│   └── synthetic_student_dataset_500_clean.csv
├── chroma_db/          ← auto-created ตอนรัน index_jobs.py
├── index_jobs.py       ← รันครั้งเดียว
├── matcher.py          ← core logic
├── main.py             ← FastAPI server
├── requirements.txt
└── README.md
```

---

## การรันโปรเจกต์ (Backend & Frontend)

โปรเจกต์นี้ประกอบด้วย 2 ส่วนหลัก คือ Backend (FastAPI) และ Frontend (Next.js) ต้องรันทั้ง 2 ส่วนพร้อมกัน (แยก Terminal)

### 1. การตั้งค่าและรัน Backend (FastAPI)

1. ติดตั้ง dependencies สำหรับ Python:
   ```bash
   pip install -r requirements.txt
   ```
2. Index job skills (ทำครั้งแรกครั้งเดียว):
   ```bash
   python index_jobs.py
   ```
   *(ใช้เวลาประมาณ 1–2 นาที จะสร้างโฟลเดอร์ `chroma_db/` ขึ้นมา)*
3. รัน API server:
   ```bash
   uvicorn main:app --reload --port 8080
   ```
   *ตรวจสอบ API Docs ได้ที่: http://localhost:8080/docs*

### 2. การตั้งค่าและรัน Frontend (Next.js)

1. เปิด Terminal ใหม่ แล้วเข้าไปที่โฟลเดอร์ `frontend`:
   ```bash
   cd frontend
   ```
2. ติดตั้ง Node.js dependencies:
   ```bash
   npm install
   ```
3. รัน Web Application:
   ```bash
   npm run dev
   ```
   *เปิด Browser ไปที่: http://localhost:3000 เพื่อใช้งานระบบ*

---

## API Endpoints

| Method | URL | คำอธิบาย |
|--------|-----|---------|
| GET | `/` | health check |
| GET | `/students` | รายชื่อนิสิตทั้งหมด |
| GET | `/students/{id}` | ข้อมูลนิสิตคนเดียว |
| POST | `/match` | match จาก skills ที่ส่งมา |
| POST | `/match/student` | match จาก student_id |
| GET | `/health` | ตรวจสอบ vector count |

---

## ตัวอย่าง Request

### Match จาก student_id
```bash
curl -X POST http://localhost:8080/match/student \
  -H "Content-Type: application/json" \
  -d '{"student_id": "6610400000", "top_n": 5}'
```

### Match จาก skills โดยตรง
```bash
curl -X POST http://localhost:8080/match \
  -H "Content-Type: application/json" \
  -d '{
    "skills": [
      {"name": "Python", "level": "Intermediate"},
      {"name": "Machine Learning", "level": "Beginner"},
      {"name": "SQL", "level": "Advanced"}
    ],
    "top_n": 5
  }'
```

### ตัวอย่าง Response
```json
{
  "student": {
    "student_id": "6610400000",
    "name": "Student_0000",
    "faculty": "Computer Engineering",
    "gpa": 3.79,
    "target_career": "Blockchain / Web3 Developer"
  },
  "top_jobs": [
    {
      "job_id": "JOB_0023",
      "job_title": "Backend Developer",
      "match_score": 0.812,
      "matched_skills": ["JavaScript / TypeScript", "SQL", "Git"],
      "skills_to_improve": [
        {
          "skill": "Docker",
          "your_level": "Beginner",
          "need_level": "Intermediate"
        }
      ],
      "missing_skills": ["Kubernetes"]
    }
  ],
  "total_student_skills": 10
}
```

---

## ต่อกับ Frontend (React/Next.js)

```javascript
// ดึง top jobs ของ student
const res = await fetch("http://localhost:8080/match/student", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ student_id: "6610400000", top_n: 5 }),
});
const data = await res.json();
console.log(data.top_jobs);
```

---

## Model ที่ใช้

`paraphrase-multilingual-MiniLM-L12-v2`
- รองรับภาษาไทย + อังกฤษ
- ขนาดเล็ก (~120MB) เร็ว เหมาะกับ demo
- โหลดจาก HuggingFace อัตโนมัติตอนรันครั้งแรก
