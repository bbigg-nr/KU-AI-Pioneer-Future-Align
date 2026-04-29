"""
services/langchain_agent.py
---------------------------
LangGraph Agent สำหรับ AI Advisor
มี 3 Tools:
  1. search_jobs — ค้นหางานจาก ChromaDB
  2. analyze_skill_gap — วิเคราะห์ช่องว่างทักษะ
  3. recommend_courses — แนะนำคอร์สเรียน

ใช้ langgraph.prebuilt.create_react_agent เพื่อลด boilerplate
"""

from __future__ import annotations

import json
import os
from typing import Any

from langchain_core.tools import tool
from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")


class AgentManager:
    """
    จัดการ LangGraph Agent + Tools ทั้งหมด
    รับ matcher และ advisor จาก main.py (dependency injection)
    """

    def __init__(
        self,
        matcher,
        advisor,
        students_dict: dict[str, dict] | None = None,
    ):
        self.matcher = matcher
        self.advisor = advisor
        self.students = students_dict or {}
        self.llm = ChatAnthropic(
            model=ANTHROPIC_MODEL,
            max_tokens=1024,
            temperature=0.1,  # ลด temperature เพื่อเพิ่ม faithfulness
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        )
        self.agent = self._build_agent()

    # ── Tool definitions ──

    def _build_agent(self):
        """สร้าง ReAct Agent พร้อม 3 tools"""

        @tool
        def search_jobs(query: str, student_skills: list[str] | None = None) -> str:
            """
            ค้นหางานที่ตรงกับนิสิตจาก ChromaDB job_skills collection
            Args:
                query: คำค้นหา เช่น "software engineer", "data scientist"
                student_skills: รายการ skills ของนิสิต (optional) ใช้ filter ผลลัพธ์
            Returns:
                รายการงานที่ตรงกับ query พร้อม relevance score และ required skills
            """
            try:
                result = self.matcher.rag_search(
                    query=query,
                    top_k_jobs=5,
                    top_k_alumni=0,
                )
                jobs = result.get("relevant_jobs", [])
                if not jobs:
                    return "ไม่พบงานที่ตรงกับคำค้นหา (No matching jobs found)."

                lines = ["🔍 งานที่แนะนำ (Recommended Jobs):"]
                for i, j in enumerate(jobs, 1):
                    skills = ", ".join(j.get("skills", [])[:6])
                    lines.append(
                        f"{i}. {j['job_title']} (relevance: {j['relevance']:.2f})\n"
                        f"   Required skills: {skills}"
                    )
                return "\n".join(lines)
            except Exception as e:
                return f"Error searching jobs: {e}"

        @tool
        def analyze_skill_gap(student_id: str, target_career: str = "") -> str:
            """
            วิเคราะห์ช่องว่างทักษะ (Skill Gap Analysis) ของนิสิต
            Args:
                student_id: รหัสนิสิต
                target_career: อาชีพเป้าหมาย (optional) ถ้าไม่ใส่จะใช้ target_career จาก profile
            Returns:
                ผลการวิเคราะห์ช่องว่างทักษะ พร้อมทักษะที่มีอยู่ ทักษะที่ขาด และทักษะที่ต้องพัฒนา
            """
            student = self.students.get(student_id)
            if not student:
                return f"ไม่พบนิสิตรหัส {student_id} (Student not found)."

            career = target_career or student.get("target_career", "")
            try:
                result = self.matcher.match(student["skills"], top_n=3)
                top_jobs = result.get("top_jobs", [])

                if not top_jobs:
                    return "ไม่พบข้อมูลการ matching (No match results)."

                # หา job ที่ตรงกับ target_career มากที่สุด หรือใช้ top-1
                target_job = top_jobs[0]
                for job in top_jobs:
                    if career.lower() in job["job_title"].lower():
                        target_job = job
                        break

                lines = [
                    f"📊 Skill Gap Analysis สำหรับ {student['name']} ({student_id})",
                    f"อาชีพเป้าหมาย: {target_job['job_title']} (match score: {target_job['match_score']:.1%})",
                    "",
                    "✅ ทักษะที่มี (Matched Skills):",
                ]
                for s in target_job.get("matched_skills", []):
                    lines.append(f"  • {s}")

                if target_job.get("skills_to_improve"):
                    lines.extend(["", "⚠️ ทักษะที่ต้องพัฒนา (Skills to Improve):"])
                    for s in target_job["skills_to_improve"]:
                        lines.append(f"  • {s['skill']}: ปัจจุบัน {s['your_level']} → ต้องการ {s['need_level']}")

                if target_job.get("missing_skills"):
                    lines.extend(["", "❌ ทักษะที่ขาด (Missing Skills):"])
                    for s in target_job["missing_skills"]:
                        lines.append(f"  • {s}")

                return "\n".join(lines)
            except Exception as e:
                return f"Error analyzing skill gap: {e}"

        @tool
        def recommend_courses(missing_skills: list[str], target_career: str = "") -> str:
            """
            แนะนำคอร์สเรียนเพื่ออัปสกิล (Upskilling Course Recommendations)
            Args:
                missing_skills: รายการทักษะที่ขาดหรือต้องพัฒนา
                target_career: อาชีพเป้าหมาย (optional)
            Returns:
                รายการคอร์สแนะนำจาก KU, Online Platforms และ Certifications
            """
            try:
                course_path = os.path.join(
                    os.path.dirname(os.path.dirname(__file__)),
                    "data",
                    "course_recommendations.json",
                )
                with open(course_path, encoding="utf-8") as f:
                    course_db = json.load(f).get("courses", {})
            except Exception as e:
                return f"Error loading course database: {e}"

            lines = ["📚 คอร์สแนะนำเพื่ออัปสกิล (Recommended Courses):"]
            found_any = False

            for skill in missing_skills:
                # fuzzy match skill name
                matched_key = None
                for key in course_db:
                    if skill.lower() in key.lower() or key.lower() in skill.lower():
                        matched_key = key
                        break

                if not matched_key:
                    continue

                found_any = True
                data = course_db[matched_key]
                lines.append(f"\n🎯 {skill}")

                if data.get("ku"):
                    lines.append("  🏫 KU Courses:")
                    for c in data["ku"]:
                        lines.append(f"    • {c['code']} — {c['title']} ({c['faculty']})")

                if data.get("online"):
                    lines.append("  💻 Online:")
                    for c in data["online"]:
                        lines.append(f"    • {c['title']} ({c['provider']}, {c['level']})")

                if data.get("cert"):
                    lines.append("  🏆 Certifications:")
                    for c in data["cert"]:
                        lines.append(f"    • {c['title']} ({c['provider']})")

            if not found_any:
                lines.append(
                    "ไม่พบคอร์สที่ตรงกับทักษะที่ระบุ (No specific courses found).\n"
                    "แนะนำให้เริ่มจากพื้นฐาน: Python, Data Structures, หรือ Statistics ก่อน"
                )

            if target_career:
                lines.append(f"\n💡 หมายเหตุ: คอร์สข้างต้นเหมาะสมสำหรับสาย {target_career}")

            return "\n".join(lines)

        @tool
        def generate_career_roadmap(student_id: str, target_career: str = "") -> str:
            """
            สร้างแผนการพัฒนาตนเอง (Career Roadmap) แนะนำเป็น Step-by-Step
            Args:
                student_id: รหัสนิสิต
                target_career: อาชีพเป้าหมาย (optional)
            Returns:
                ข้อมูลแผน Roadmap เบื้องต้นตามชั้นปีและทักษะที่ขาด
            """
            student = self.students.get(student_id)
            if not student:
                return f"ไม่พบนิสิตรหัส {student_id}"
            
            career = target_career or student.get("target_career", "")
            year = str(student.get("year", "3"))
            
            try:
                result = self.matcher.match(student["skills"], top_n=3)
                top_jobs = result.get("top_jobs", [])
                target_job = top_jobs[0] if top_jobs else None
                for job in top_jobs:
                    if career.lower() in job["job_title"].lower():
                        target_job = job
                        break
                        
                missing_skills = target_job.get("missing_skills", []) if target_job else []
                improve_skills = [s["skill"] for s in target_job.get("skills_to_improve", [])] if target_job else []
                
            except Exception:
                missing_skills = []
                improve_skills = []

            lines = [
                f"🗺️ Career Roadmap สำหรับ {student['name']} (ปี {year})",
                f"มุ่งสู่เส้นทาง: {career}",
                "",
                "📍 ระยะสั้น (1-2 เทอมถัดไป) - ปิดช่องว่างทักษะสำคัญ:",
            ]
            if missing_skills:
                lines.append(f"  • เริ่มศึกษาทักษะใหม่: {', '.join(missing_skills)}")
            if improve_skills:
                lines.append(f"  • พัฒนาทักษะเดิม: {', '.join(improve_skills)}")
                
            lines.extend([
                "",
                "📍 ระยะกลาง (ก่อนจบการศึกษา) - เก็บเกี่ยวประสบการณ์:",
                "  • ทำโปรเจกต์ที่เกี่ยวข้องกับทักษะข้างต้น",
                "  • หาที่ฝึกงานในบริษัทที่เกี่ยวข้องกับสายงาน",
                "",
                "📍 ระยะยาว (หลังเรียนจบ) - การเติบโตในสายงาน:",
                f"  • สมัครงานในตำแหน่ง Junior {career}",
                "  • สานต่อการเรียนรู้เทคโนโลยีใหม่ๆ ในอุตสาหกรรม"
            ])
            
            return "\n".join(lines)

        tools = [search_jobs, analyze_skill_gap, recommend_courses, generate_career_roadmap]

        # สร้าง ReAct Agent
        self.agent_tools = tools
        self.system_instructions = """You are FutureAlign AI Advisor, a career guidance assistant for Kasetsart University (KU) students.

## Available Tools
1. search_jobs — ค้นหางานจาก ChromaDB ตาม query และ skills
2. analyze_skill_gap — วิเคราะห์ช่องว่างทักษะของนิสิต (ต้องใช้ student_id)
3. recommend_courses — แนะนำคอร์สเรียนเพื่ออัปสกิลจาก missing skills
4. generate_career_roadmap — สร้างแผนการพัฒนาตนเองตามชั้นปี (ต้องใช้ student_id)

## CRITICAL RULES (STRICT — FOLLOW EXACTLY)
- The student's profile (including student_id) is ALWAYS provided in the context below. NEVER ask the user for their student_id or skills.
- When the user asks about jobs, career matches, or roles → IMMEDIATELY call search_jobs tool using their skills from the profile. Do NOT ask for more info.
- When the user asks about skill gap, missing skills, or skill analysis → IMMEDIATELY call analyze_skill_gap with the EXACT student_id provided in the profile. Do NOT ask for student_id again.
- When the user asks about courses, learning, or upskilling → IMMEDIATELY call recommend_courses with relevant skills. Do NOT ask for more info.
- When the user asks for a roadmap, plan, or steps to reach their career goal → IMMEDIATELY call generate_career_roadmap with the EXACT student_id. Do NOT ask for student_id again.
- You MAY call multiple tools in sequence if the user asks for multiple things.

## GROUNDING RULES (MUST FOLLOW TO PREVENT HALLUCINATION)
1. **USE TOOL RESULTS ONLY**: After receiving tool results, you MUST base your answer ONLY on the data returned by the tools. Do NOT use external knowledge, assumptions, or made-up facts.
2. **NO HALLUCINATION**: If a tool returns "No matching jobs found" or empty data, tell the user honestly. Do NOT invent job titles, salary numbers, or alumni stories.
3. **CITE DATA**: Reference specific numbers, job titles, and skill names exactly as they appear in tool results.
4. **SAME LANGUAGE**: Respond in the SAME language the user writes (Thai or English).
5. **CONCISENESS**: Keep responses concise (3-5 sentences) unless detail is explicitly requested.
6. **TONE**: Be encouraging, specific, and reference actual data from tool results."""

        agent = create_react_agent(
            model=self.llm,
            tools=tools,
        )
        return agent

    # ── Public interface ──

    def _build_student_context(self, student_id: str) -> str:
        """สร้าง student context string สำหรับ inject เข้า agent"""
        student = self.students.get(student_id)
        if not student:
            return ""
        skills_str = ', '.join(f"{s['name']} ({s['level']})" for s in student.get('skills', []))
        return (
            f"[STUDENT PROFILE]\n"
            f"student_id: {student_id}\n"
            f"Name: {student.get('name', 'N/A')}\n"
            f"Faculty: {student.get('faculty', 'N/A')}\n"
            f"Year: {student.get('year', 'N/A')}, GPA: {student.get('gpa', 'N/A')}\n"
            f"Skills: {skills_str}\n"
            f"Target career: {student.get('target_career', 'N/A')}\n"
            f"Activities: {student.get('activities', 'N/A')}\n"
            f"\nUSE THE ABOVE student_id ({student_id}) DIRECTLY when calling analyze_skill_gap."
        )

    def invoke(
        self,
        messages: list[dict],
        student_id: str | None = None,
        system_context: str | None = None,
    ) -> dict[str, Any]:
        """
        เรียก Agent ด้วย messages + optional student context
        Returns: { "text": str, "tools_used": list[str] }
        """
        from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

        # System message: instructions + optional system_context
        system_parts = [self.system_instructions]
        if system_context:
            system_parts.append(system_context)

        full_system = "\n".join(system_parts)
        langchain_messages: list = [SystemMessage(content=full_system)]

        # Inject student profile as a hidden user message BEFORE actual user messages
        # This ensures the agent "sees" it as user-provided context
        if student_id and student_id in self.students:
            student_ctx = self._build_student_context(student_id)
            langchain_messages.append(HumanMessage(content=student_ctx))
            # Add a synthetic assistant acknowledgment so the model knows it's been noted
            langchain_messages.append(AIMessage(content="Got it. I have your student profile loaded."))

        for m in messages:
            if m["role"] == "user":
                langchain_messages.append(HumanMessage(content=m["content"]))
            elif m["role"] == "assistant":
                langchain_messages.append(AIMessage(content=m["content"]))

        # เรียก agent
        result = self.agent.invoke({"messages": langchain_messages})
        output_messages = result.get("messages", [])

        # ดึง final assistant message
        final_text = ""
        tools_used: list[str] = []

        for msg in output_messages:
            # tool calls
            if getattr(msg, "tool_calls", None):
                for tc in msg.tool_calls:
                    tools_used.append(tc.get("name", "unknown"))
            # เนื้อหาสุดท้าย
            if getattr(msg, "type", None) == "ai" and msg.content:
                final_text = msg.content

        return {
            "text": final_text,
            "tools_used": list(dict.fromkeys(tools_used)),  # dedup preserve order
        }
