"""
services/pdf_extractor.py
-------------------------
PDF Resume/Portfolio skill extractor
ย้ายมาจาก frontend/app/api/extract-skills/route.ts
ใช้ Anthropic Claude Haiku บน backend
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """You are an expert resume and portfolio parser.
Extract skills and activities from the provided PDF document.

Return ONLY valid JSON in this exact format (no markdown, no extra text):
{
  "skills": [
    { "name": "Skill Name", "level": "Beginner|Intermediate|Advanced" }
  ],
  "activities": [
    "[Role] at [Organization or Project Name Year]"
  ]
}

Rules for skills:
- Include both technical skills (programming, tools, frameworks) and soft skills (leadership, communication)
- Infer level from context clues: years of experience, project complexity, certifications
  - Beginner: mentioned briefly, < 1 year, basic familiarity
  - Intermediate: used in projects, 1-3 years
  - Advanced: expert, >3 years, taught others, led projects using this skill
- Deduplicate and normalize skill names (e.g. "JS" → "JavaScript")
- Skip generic filler like "Microsoft Office" unless clearly mentioned

Rules for activities:
- Format MUST be: [Role] at [Organization or Project Year]
- Extract extracurricular, internships, club leadership, competitions, volunteer work, research
- If year is mentioned, include it in the organization part
- Keep each activity concise and descriptive
- Do NOT include regular coursework or classes

If nothing can be extracted for a category, return an empty array."""


class PDFSkillExtractor:
    """Extract skills and activities from PDF resume using Claude Haiku."""

    def __init__(self):
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = os.getenv("ANTHROPIC_PDF_MODEL", "claude-haiku-4-5-20251001")

    def extract(self, pdf_bytes: bytes) -> dict[str, Any]:
        """
        รับ PDF bytes → คืน {skills: list[dict], activities: list[str]}
        """
        import base64

        base64_data = base64.b64encode(pdf_bytes).decode("utf-8")

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "document",
                            "source": {
                                "type": "base64",
                                "media_type": "application/pdf",
                                "data": base64_data,
                            },
                        },
                        {
                            "type": "text",
                            "text": "Extract all skills and activities from this document.",
                        },
                    ],
                }
            ],
        )

        raw = ""
        if response.content and len(response.content) > 0:
            raw = response.content[0].text if hasattr(response.content[0], "text") else str(response.content[0])

        cleaned = raw.strip()
        # ลบ markdown code block ถ้ามี
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            # Fallback: พยายาม extract JSON จาก text
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if match:
                try:
                    parsed = json.loads(match.group(0))
                except json.JSONDecodeError:
                    parsed = {"skills": [], "activities": []}
            else:
                parsed = {"skills": [], "activities": []}

        return {
            "skills": parsed.get("skills", []) if isinstance(parsed.get("skills"), list) else [],
            "activities": parsed.get("activities", []) if isinstance(parsed.get("activities"), list) else [],
        }
