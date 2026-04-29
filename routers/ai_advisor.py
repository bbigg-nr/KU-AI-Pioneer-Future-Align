"""
routers/ai_advisor.py
---------------------
FastAPI router สำหรับ AI Advisor endpoints
- POST /ai/advisor/chat
- POST /ai/extract-skills
"""

from __future__ import annotations

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Any

from services.langchain_agent import AgentManager
from services.pdf_extractor import PDFSkillExtractor

router = APIRouter(prefix="/ai", tags=["AI Advisor"])

# ── Schemas ──

class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str

class AdvisorChatRequest(BaseModel):
    messages: list[ChatMessage]
    student_id: str | None = None
    system_context: str | None = None

class AdvisorChatResponse(BaseModel):
    text: str
    rag_used: bool = False
    tools_used: list[str] = []

class ExtractSkillsResponse(BaseModel):
    skills: list[dict]
    activities: list[str]


# ── Dependency: AgentManager singleton ──
_agent_manager: AgentManager | None = None
_pdf_extractor: PDFSkillExtractor | None = None


def get_agent_manager() -> AgentManager:
    if _agent_manager is None:
        raise HTTPException(status_code=503, detail="AI Advisor not initialized")
    return _agent_manager


def get_pdf_extractor() -> PDFSkillExtractor:
    global _pdf_extractor
    if _pdf_extractor is None:
        _pdf_extractor = PDFSkillExtractor()
    return _pdf_extractor


def set_agent_manager(manager: AgentManager):
    global _agent_manager
    _agent_manager = manager


# ── Endpoints ──

@router.post("/advisor/chat", response_model=AdvisorChatResponse)
def advisor_chat(req: AdvisorChatRequest):
    """
    AI Advisor Chat — LangGraph Agent พร้อม 3 Tools
    """
    manager = get_agent_manager()

    messages = [{"role": m.role, "content": m.content} for m in req.messages]

    # สร้าง system context ถ้ามี student_id แต่ไม่มี system_context
    system_context = req.system_context
    if not system_context and req.student_id:
        student = manager.students.get(req.student_id)
        if student:
            # ดึง RAG context
            retrieval = manager.advisor.build_retrieval_chain()
            last_user_msg = next(
                (m for m in reversed(messages) if m["role"] == "user"),
                None,
            )
            query = last_user_msg["content"] if last_user_msg else ""
            enriched_query = f"{query} {' '.join(s['name'] for s in student.get('skills', []))} {student.get('target_career', '')}"
            rag_result = retrieval(enriched_query)

            student_ctx = {
                "name": student.get("name", ""),
                "faculty": student.get("faculty", ""),
                "year": student.get("year", ""),
                "gpa": student.get("gpa", ""),
                "skills": student.get("skills", []),
                "languages": student.get("languages", []),
                "target_career": student.get("target_career", ""),
                "activities": student.get("activities", ""),
            }
            system_context = manager.advisor.build_system_context(student_ctx, rag_result)

    result = manager.invoke(
        messages=messages,
        student_id=req.student_id,
        system_context=system_context,
    )

    return AdvisorChatResponse(
        text=result["text"],
        rag_used=bool(system_context and "Retrieved Context" in system_context),
        tools_used=result.get("tools_used", []),
    )


@router.post("/extract-skills", response_model=ExtractSkillsResponse)
async def extract_skills(pdf: UploadFile = File(...)):
    """
    Extract skills and activities from uploaded PDF resume
    """
    extractor = get_pdf_extractor()

    if pdf.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="File must be a PDF")

    contents = await pdf.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="PDF must be under 10 MB")

    try:
        result = extractor.extract(contents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {e}")

    return ExtractSkillsResponse(
        skills=result.get("skills", []),
        activities=result.get("activities", []),
    )
