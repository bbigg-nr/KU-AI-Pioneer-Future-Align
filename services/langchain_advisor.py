"""
services/langchain_advisor.py
-----------------------------
LangChain RAG Pipeline + Advanced Prompt Engineering สำหรับ AI Advisor

เชื่อมต่อกับ ChromaDB ผ่าน langchain_chroma.Chroma
ใช้ RunnableParallel ดึง context จาก job_skills + alumni_rag_profiles พร้อมกัน
"""

from __future__ import annotations

import json
import os
from typing import Any

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_anthropic import ChatAnthropic
from dotenv import load_dotenv

load_dotenv()

# ── Constants ──
CHROMA_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")
MODEL_NAME = os.getenv("HF_MODEL_NAME", "paraphrase-multilingual-MiniLM-L12-v2")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20240620")

# ── System prompt template ──
SYSTEM_TEMPLATE = """You are **FutureAlign AI Advisor**, a career guidance assistant for Kasetsart University (KU) students.

## Student Profile
- Name: {name}
- Faculty: {faculty}
- Year: {year}, GPA: {gpa}
- Skills: {skills}
- Languages: {languages}
- Target career: {target_career}
{top_job_line}
{activities_line}

## Retrieved Context
{retrieved_context}

## CRITICAL INSTRUCTIONS (STRICT — FOLLOW EXACTLY)
1. **GROUNDING RULE**: You MUST base your answer **ONLY** on the Retrieved Context above and the Student Profile. Do NOT use any external knowledge, assumptions, or hallucinated facts.
2. **NO INFO RULE**: If the Retrieved Context does not contain information needed to answer the user's question, explicitly state: "ขออภัย ระบบไม่มีข้อมูลในฐานข้อมูลที่ตอบคำถามนี้ได้โดยตรง" (or "Sorry, I don't have specific data in the retrieved context to answer that.") and then suggest a related question you CAN answer from the context.
3. **CITATION RULE**: When mentioning any job title, skill, salary, or alumni outcome, you MUST link it to a specific item in the Retrieved Context. Do not invent numbers, job titles, or alumni stories.
4. **LANGUAGE**: Answer in the **same language** the user writes (Thai or English).
5. **TONE**: Be encouraging, specific, and actionable.
6. **CONCISENESS**: Keep responses concise (3-5 sentences unless detail is needed). Use bullet points for lists.
7. **TOOLS**: If asked about skill gaps, use the analyze_skill_gap tool. If asked about job matches, use the search_jobs tool. If asked about courses or upskilling, use the recommend_courses tool."""


class LangChainAdvisor:
    """
    Central service สำหรับจัดการ RAG + Prompt Engineering
    ใช้ ChromaDB collections ที่มีอยู่แล้ว (job_skills, alumni_rag_profiles)
    """

    def __init__(
        self,
        embedding_model=None,
        chroma_client=None,
    ):
        # ใช้ embedding model จาก matcher.py ถ้ามี (ไม่ต้องโหลดซ้ำ)
        self.embedding_model = embedding_model

        # สร้าง Chroma vector stores จาก client ที่มีอยู่
        self.job_store = Chroma(
            client=chroma_client,
            collection_name="job_skills",
            embedding_function=self._wrap_embedding(),
        )
        self.alumni_store = Chroma(
            client=chroma_client,
            collection_name="alumni_rag_profiles",
            embedding_function=self._wrap_embedding(),
        )

        # NEW: job_summaries collection มี context ครบกว่า (title + industry + skills + salary)
        # ช่วยให้ LLM ตอบได้ grounded มากขึ้น → เพิ่ม Faithfulness
        try:
            self.job_summary_store = Chroma(
                client=chroma_client,
                collection_name="job_summaries",
                embedding_function=self._wrap_embedding(),
            )
            # quick check ว่า collection มีข้อมูลหรือไม่
            self._has_job_summaries = self.job_summary_store._collection.count() > 0
        except Exception:
            self.job_summary_store = None
            self._has_job_summaries = False

        # Retrievers — ใช้ similarity_score_threshold เพื่อกรองเอกสารที่ relevance ต่ำออก
        # ถ้ามี job_summaries ใช้เป็นหลัก (context ครบกว่า) ไม่มีก็ fallback ไป job_skills
        if self._has_job_summaries:
            self.job_retriever = self.job_summary_store.as_retriever(
                search_type="similarity_score_threshold",
                search_kwargs={"k": 5, "score_threshold": 0.50},
            )
            self.job_fallback_retriever = self.job_store.as_retriever(
                search_type="similarity_score_threshold",
                search_kwargs={"k": 8, "score_threshold": 0.55},
            )
        else:
            self.job_retriever = self.job_store.as_retriever(
                search_type="similarity_score_threshold",
                search_kwargs={"k": 8, "score_threshold": 0.55},
            )
            self.job_fallback_retriever = None

        self.alumni_retriever = self.alumni_store.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={"k": 5, "score_threshold": 0.55},
        )

        # LLM — ลด temperature เพื่อให้ยึดตาม context มากขึ้น (เพิ่ม faithfulness)
        self.llm = ChatAnthropic(
            model=ANTHROPIC_MODEL,
            max_tokens=1024,
            temperature=0.1,
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        )

        # Prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_TEMPLATE),
            MessagesPlaceholder(variable_name="messages"),
        ])

    # ── Internal helpers ──

    def _wrap_embedding(self):
        """Wrap existing SBERT model ให้เข้ากับ LangChain Embeddings interface."""
        from langchain_core.embeddings import Embeddings

        class _Wrapper(Embeddings):
            def __init__(self, model):
                self.model = model

            def embed_documents(self, texts: list[str]) -> list[list[float]]:
                if self.model is None:
                    raise RuntimeError("Embedding model not provided")
                embs = self.model.encode(texts, batch_size=32)
                return embs.tolist()

            def embed_query(self, text: str) -> list[float]:
                if self.model is None:
                    raise RuntimeError("Embedding model not provided")
                return self.model.encode([text])[0].tolist()

        return _Wrapper(self.embedding_model)

    def _format_docs(self, docs: list[Document]) -> str:
        lines: list[str] = []
        for d in docs:
            meta = d.metadata
            # รองรับทั้ง job_skills (per-skill) และ job_summaries (full context)
            if "skills_text" in meta:
                # format จาก job_summaries collection
                lines.append(
                    f"- {meta.get('job_title', 'Job')} ({meta.get('industry', 'N/A')}) — "
                    f"Salary: {meta.get('min_salary', 'N/A')}-{meta.get('max_salary', 'N/A')} THB | "
                    f"Skills: {meta.get('skills_text', 'N/A')}"
                )
            else:
                # format จาก job_skills collection (per-skill)
                lines.append(
                    f"- {meta.get('job_title', 'Job')} | Skill: {meta.get('skill_name', 'N/A')} "
                    f"({meta.get('level', 'N/A')})"
                )
        return "\n".join(lines) if lines else "No relevant jobs found."

    def _format_alumni(self, docs: list[Document]) -> str:
        lines: list[str] = []
        for d in docs:
            meta = d.metadata
            lines.append(
                f"- {meta.get('first_job_title', 'Alumnus')} ({meta.get('faculty', 'N/A')}) — "
                f"salary start ฿{meta.get('salary_start', 'N/A'):,}, "
                f"promoted in {meta.get('years_to_promotion', 'N/A')} yr(s), "
                f"success score {meta.get('success_score', 'N/A')}/99"
            )
        return "\n".join(lines) if lines else "No relevant alumni found."

    # ── Public methods ──

    def build_retrieval_chain(self):
        """
        สร้าง Runnable chain ที่ดึง RAG context จาก jobs + alumni พร้อมกัน
        พร้อมกรองเอกสารที่ relevance ต่ำเกินไปออก (fallback ถ้า retriever ไม่กรองให้)
        """
        def _retrieve(query: str) -> dict[str, Any]:
            jobs = self.job_retriever.invoke(query)

            # Fallback: ถ้า job_summaries ไม่คืนผลลัพธ์ ให้ลอง job_skills
            if (not jobs or len(jobs) == 0) and self.job_fallback_retriever is not None:
                jobs = self.job_fallback_retriever.invoke(query)

            alumni = self.alumni_retriever.invoke(query)

            # Safety filter: ถ้า retriever คืนมากเกินไป ให้ตัดเหลือ top-k ที่ดีที่สุด
            jobs = jobs[:6]
            alumni = alumni[:4]

            return {
                "jobs": jobs,
                "alumni": alumni,
                "jobs_text": self._format_docs(jobs),
                "alumni_text": self._format_alumni(alumni),
            }

        return _retrieve

    def build_system_context(
        self,
        student: dict | None,
        retrieval_result: dict,
    ) -> str:
        """
        สร้าง system context string จาก student profile + RAG retrieval
        """
        if student is None:
            student = {}

        skills = ", ".join(
            f"{s['name']} ({s['level']})" for s in student.get("skills", [])
        ) or "N/A"
        languages = ", ".join(
            f"{l['name']} ({l['level']})" for l in student.get("languages", [])
        ) or "N/A"
        top_job_line = ""
        if student.get("top_job"):
            score = student.get("top_job_score", 0)
            top_job_line = f"- Top career match: {student['top_job']} ({int(score * 100)}% match)"

        activities_line = ""
        if student.get("activities"):
            activities_line = f"- Activities & Experience: {student['activities']}"

        retrieved = ""
        if retrieval_result.get("jobs_text"):
            retrieved += f"### Relevant Job Listings\n{retrieval_result['jobs_text']}\n\n"
        if retrieval_result.get("alumni_text"):
            retrieved += f"### Similar Alumni Profiles\n{retrieval_result['alumni_text']}\n\n"
        if not retrieved:
            retrieved = "No retrieved context."

        return self.prompt.format_messages(
            name=student.get("name", "Student"),
            faculty=student.get("faculty", "N/A"),
            year=student.get("year", "N/A"),
            gpa=student.get("gpa", "N/A"),
            skills=skills,
            languages=languages,
            target_career=student.get("target_career", "N/A"),
            top_job_line=top_job_line,
            activities_line=activities_line,
            retrieved_context=retrieved,
            messages=[],  # messages จะถูกแทรกทีหลัง
        )[0].content

    def stream_chat(
        self,
        messages: list[dict],
        system_context: str,
    ):
        """
        Stream response จาก Claude ผ่าน LangChain
        messages: list of {"role": "user"|"assistant", "content": str}
        """
        from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

        langchain_messages: list = [SystemMessage(content=system_context)]
        for m in messages:
            if m["role"] == "user":
                langchain_messages.append(HumanMessage(content=m["content"]))
            elif m["role"] == "assistant":
                langchain_messages.append(AIMessage(content=m["content"]))

        return self.llm.stream(langchain_messages)

    def invoke_chat(
        self,
        messages: list[dict],
        system_context: str,
    ) -> str:
        """
        Non-streaming chat — คืน text เต็ม
        """
        from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

        langchain_messages: list = [SystemMessage(content=system_context)]
        for m in messages:
            if m["role"] == "user":
                langchain_messages.append(HumanMessage(content=m["content"]))
            elif m["role"] == "assistant":
                langchain_messages.append(AIMessage(content=m["content"]))

        response = self.llm.invoke(langchain_messages)
        return response.content
