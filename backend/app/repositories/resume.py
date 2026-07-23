from typing import List, Optional
import uuid
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resume import Resume, ResumeAnalysis, Skill, Education, Experience, Certification
from app.repositories.base import BaseRepository

class ResumeRepository(BaseRepository[Resume]):
    def __init__(self, db: AsyncSession):
        super().__init__(Resume, db)

    async def get_by_id_fully_loaded(self, id: uuid.UUID) -> Optional[Resume]:
        """Fetch a single resume by ID, eagerly loading all nested relations."""
        query = (
            select(Resume)
            .where(Resume.id == id)
            .where(Resume.deleted_at == None)
            .options(
                selectinload(Resume.analysis),
                selectinload(Resume.skills),
                selectinload(Resume.education),
                selectinload(Resume.experience),
                selectinload(Resume.certifications)
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_all_user_resumes(self, user_id: uuid.UUID) -> List[Resume]:
        """Fetch all non-deleted resumes uploaded by a specific user, loading analysis scores."""
        query = (
            select(Resume)
            .where(Resume.user_id == user_id)
            .where(Resume.deleted_at == None)
            .options(
                selectinload(Resume.analysis),
                selectinload(Resume.skills),
                selectinload(Resume.education),
                selectinload(Resume.experience),
                selectinload(Resume.certifications)
            )
            .order_by(Resume.created_at.desc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create_resume_hierarchy(
        self,
        user_id: uuid.UUID,
        file_name: str,
        file_url: str,
        file_size: int,
        parsed_data: dict,
        scored_result: dict
    ) -> Resume:
        """Transactionally create the full resume relational tree in the database."""
        # 1. Create primary Resume record
        resume = Resume(
            user_id=user_id,
            file_name=file_name,
            file_url=file_url,
            file_size=file_size,
            raw_text=parsed_data.get("raw_text")
        )
        self.db.add(resume)
        await self.db.flush()  # Populates resume.id for foreign keys

        # 2. Add Skills
        for skill_in in parsed_data.get("skills", []):
            skill = Skill(
                resume_id=resume.id,
                name=skill_in.get("name"),
                category=skill_in.get("category")
            )
            self.db.add(skill)

        # 3. Add Education entries
        for edu_in in parsed_data.get("education", []):
            edu = Education(
                resume_id=resume.id,
                institution=edu_in.get("institution"),
                degree=edu_in.get("degree"),
                field_of_study=edu_in.get("field_of_study"),
                start_date=edu_in.get("start_date"),
                end_date=edu_in.get("end_date"),
                description=edu_in.get("description")
            )
            self.db.add(edu)

        # 4. Add Experience entries
        for exp_in in parsed_data.get("experience", []):
            exp = Experience(
                resume_id=resume.id,
                company=exp_in.get("company"),
                position=exp_in.get("position"),
                location=exp_in.get("location"),
                start_date=exp_in.get("start_date"),
                end_date=exp_in.get("end_date"),
                description=exp_in.get("description")
            )
            self.db.add(exp)

        # 5. Add Certifications
        for cert_in in parsed_data.get("certifications", []):
            cert = Certification(
                resume_id=resume.id,
                name=cert_in.get("name"),
                issuing_organization=cert_in.get("issuing_organization"),
                issue_date=cert_in.get("issue_date"),
                expiration_date=cert_in.get("expiration_date")
            )
            self.db.add(cert)

        # 6. Add Resume Analysis score and feedback
        analysis = ResumeAnalysis(
            resume_id=resume.id,
            ats_score=scored_result.get("ats_score", 0),
            feedback=scored_result.get("feedback", {}),
            extracted_data=scored_result.get("extracted_data", {})
        )
        self.db.add(analysis)

        await self.db.flush()
        return resume
