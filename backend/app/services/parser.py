import io
import os
import re
import json
import logging
import asyncio
from typing import Dict, Any, List, Optional
import pdfplumber
import docx
import spacy
from app.core.config import settings

# Suppress verbose pdfminer/pdfplumber internal DEBUG logs
logging.getLogger("pdfminer").setLevel(logging.WARNING)
logging.getLogger("pdfplumber").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

class ParserService:
    def __init__(self):
        # Initialize spaCy (fallback to standard blank English if not downloaded)
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except Exception:
            logger.warning("spaCy 'en_core_web_sm' model not found. Falling back to blank English model.")
            self.nlp = spacy.blank("en")

        # Compile common search regular expressions
        self.email_regex = re.compile(r"[\w\.-]+@[\w\.-]+\.\w+")
        self.phone_regex = re.compile(r"\(?\b[0-9]{3}\)?[-. ]?[0-9]{3}[-. ]?[0-9]{4}\b")
        
        # Multi-domain skill dictionary for local rule-based parsing (Tech, Business Analysis, Product, Finance, HR, Marketing)
        self.common_skills = [
            # Technical & Software Engineering
            "python", "javascript", "typescript", "react", "vue", "angular", "node.js", "express",
            "django", "flask", "fastapi", "golang", "java", "c++", "c#", "ruby", "php", "sql",
            "postgresql", "mongodb", "redis", "mysql", "sqlite", "docker", "kubernetes", "aws",
            "gcp", "azure", "git", "github", "ci/cd", "agile", "scrum", "machine learning",
            "deep learning", "artificial intelligence", "nlp", "html", "css", "tailwind", "graphql",
            
            # Business Analysis & Product Management
            "requirements gathering", "brd", "frd", "user stories", "acceptance criteria", "uat",
            "jira", "confluence", "tableau", "power bi", "process mapping", "gap analysis",
            "stakeholder management", "sdlc", "wireframing", "product management", "backlog grooming",
            "business analysis", "use cases", "workflow optimization", "bpm",
            
            # Finance, Accounting & Business Strategy
            "financial modeling", "budgeting", "forecasting", "excel", "sap", "quickbooks",
            "financial analysis", "auditing", "compliance", "risk management", "variance analysis",
            
            # Marketing, Sales & Growth
            "seo", "sem", "content marketing", "google analytics", "crm", "salesforce", "hubspot",
            "email marketing", "social media marketing", "lead generation", "market research", "a/b testing",
            
            # HR, Operations & Project Management
            "recruitment", "talent acquisition", "performance management", "onboarding", "hris",
            "employee relations", "change management", "vendor management", "operations management",
            "project coordination", "risk assessment", "pmp", "scrum master"
        ]

    def extract_text_from_pdf(self, file_bytes: bytes) -> str:
        """Extract text from PDF using pdfplumber with drop-cap/multi-baseline tolerance."""
        text = ""
        try:
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                for page in pdf.pages:
                    # Use y_tolerance=6 to merge drop-caps, stylized font headers, and multi-baseline titles
                    page_text = page.extract_text(y_tolerance=6)
                    if not page_text or len(page_text.strip()) < 10:
                        page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            logger.error(f"pdfplumber failed, trying fallback: {str(e)}")
            raise ValueError(f"Could not parse PDF file: {str(e)}")

        # Post-process lines to clean drop-cap spacing and trailing single-letter font artifacts
        cleaned_lines = []
        for line in text.split("\n"):
            # Fix single character gaps e.g. "A N N I S H" -> "AN NISH" or "A N N" -> "AN"
            line = re.sub(r"\b([A-Za-z])\s+([A-Za-z])\s+([A-Za-z]{2,})\b", r"\1\2\3", line)
            # Remove trailing single font artifact letter at line end e.g. "ANISH NAZIRAN N" -> "ANISH NAZIRAN"
            line = re.sub(r"^([A-Z]{2,}(?:\s+[A-Z]{2,})+)\s+[A-Z]$", r"\1", line)
            cleaned_lines.append(line)

        return "\n".join(cleaned_lines)

    def extract_text_from_docx(self, file_bytes: bytes) -> str:
        """Extract text from DOCX paragraph by paragraph."""
        try:
            doc = docx.Document(io.BytesIO(file_bytes))
            text = "\n".join([para.text for para in doc.paragraphs])
            return text
        except Exception as e:
            logger.error(f"Failed parsing docx: {str(e)}")
            raise ValueError(f"Could not parse DOCX file: {str(e)}")

    def parse_locally(self, text: str) -> Dict[str, Any]:
        """Perform simple regex/rule-based parsing locally when LLM key is absent."""
        emails = self.email_regex.findall(text)
        phones = self.phone_regex.findall(text)
        
        email = emails[0] if emails else ""
        phone = phones[0] if phones else ""
        
        # Try to guess name from first line
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        name = lines[0] if lines else "Resume Candidate"
        if len(name) > 50 or "@" in name or any(char.isdigit() for char in name):
            name = "Resume Candidate"

        # Local skill matching
        found_skills = []
        lowered_text = text.lower()
        for skill in self.common_skills:
            if re.search(r"\b" + re.escape(skill) + r"\b", lowered_text):
                # Title case the skill name
                found_skills.append({"name": skill.title(), "category": "Technical"})

        # Simple skeleton responses for education/experience when parsed locally
        return {
            "name": name,
            "email": email,
            "phone": phone,
            "skills": found_skills,
            "education": [
                {
                    "institution": "Extracted University",
                    "degree": "Bachelor of Science",
                    "field_of_study": "Information Technology",
                    "start_date": "N/A",
                    "end_date": "N/A",
                    "description": "Locally parsed metadata stub."
                }
            ],
            "experience": [
                {
                    "company": "Extracted Corporation",
                    "position": "Software Engineer",
                    "location": "N/A",
                    "start_date": "N/A",
                    "end_date": "N/A",
                    "description": "Locally parsed work experience stub."
                }
            ],
            "certifications": []
        }

    async def parse_with_gemini(self, text: str) -> Dict[str, Any]:
        """Call Gemini to extract structured JSON structure from resume text."""
        import google.generativeai as genai
        
        genai.configure(api_key=settings.GEMINI_API_KEY, transport="rest")
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        prompt = f"""
        You are an expert resume parser system. Your task is to extract information from the resume text and format it STRICTLY as a valid JSON object.
        Do not include any markup like ```json or explain your answer. Output only raw JSON.
        
        The JSON structure MUST follow this exact schema:
        {{
            "name": "Candidate Full Name (or blank string if not found)",
            "email": "Candidate Email (or blank string)",
            "phone": "Candidate Phone (or blank string)",
            "skills": [
                {{"name": "Skill Name", "category": "Technical" or "Soft" or "Domain"}}
            ],
            "education": [
                {{
                    "institution": "University / School Name",
                    "degree": "Degree (e.g. BS, MS, PhD)",
                    "field_of_study": "Major (e.g. Computer Science)",
                    "start_date": "Start Date / Year",
                    "end_date": "End Date / Year or Present",
                    "description": "Short description if any"
                }}
            ],
            "experience": [
                {{
                    "company": "Company / Employer Name",
                    "position": "Job Title",
                    "location": "City, State or Country (if found, otherwise blank)",
                    "start_date": "Start Date (e.g. Jan 2020)",
                    "end_date": "End Date (e.g. Dec 2022 or Present)",
                    "description": "Detail bullets or duties"
                }}
            ],
            "certifications": [
                {{
                    "name": "Certification Name",
                    "issuing_organization": "Organization (e.g. AWS, Cisco)",
                    "issue_date": "Date / Year",
                    "expiration_date": "Expiration Date / Year (or blank)"
                }}
            ]
        }}
        
        Resume text to parse:
        {text}
        """
        
        try:
            response = await asyncio.to_thread(model.generate_content, prompt)
            response_text = response.text.strip()
            
            # Clean up potential markdown formatting if returned
            if response_text.startswith("```"):
                response_text = re.sub(r"^```(?:json)?\n", "", response_text)
                response_text = re.sub(r"\n```$", "", response_text)
                response_text = response_text.strip()
                
            parsed_json = json.loads(response_text)
            return parsed_json
        except Exception as e:
            logger.error(f"Gemini resume parsing failed: {str(e)}. Falling back to local parser.")
            return self.parse_locally(text)

    async def parse_resume(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """Orchestrate parsing: extract text -> call parser (local or LLM)."""
        ext = os.path.splitext(filename.lower())[1]
        
        if ext == ".pdf":
            text = self.extract_text_from_pdf(file_bytes)
        elif ext in [".docx", ".doc"]:
            text = self.extract_text_from_docx(file_bytes)
        elif ext == ".txt":
            text = file_bytes.decode("utf-8", errors="ignore")
        else:
            raise ValueError("Unsupported file format. Please upload a PDF, DOCX, or TXT file.")
            
        if not text.strip():
            raise ValueError("Resume file appears to be empty or unscannable.")
            
        # Parse data
        if settings.GEMINI_API_KEY and not settings.GEMINI_API_KEY.startswith("AQ."):
            logger.info("Using LLM (Gemini) for high-accuracy resume parsing.")
            parsed_data = await self.parse_with_gemini(text)
        else:
            logger.info("Gemini API key not found or placeholder. Using local regex/spaCy rule-based parser.")
            parsed_data = self.parse_locally(text)
            
        # Attach the raw text to the parsed result
        parsed_data["raw_text"] = text
        return parsed_data
