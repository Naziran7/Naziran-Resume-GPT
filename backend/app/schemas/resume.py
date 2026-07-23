import uuid
from datetime import datetime
from typing import List, Optional, Any
from pydantic import BaseModel, ConfigDict

class RescoreRequest(BaseModel):
    target_job_description: Optional[str] = None

class SkillSchema(BaseModel):
    name: str
    category: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class EducationSchema(BaseModel):
    institution: str
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class ExperienceSchema(BaseModel):
    company: str
    position: str
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class CertificationSchema(BaseModel):
    name: str
    issuing_organization: Optional[str] = None
    issue_date: Optional[str] = None
    expiration_date: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class ResumeAnalysisResponse(BaseModel):
    id: uuid.UUID
    resume_id: uuid.UUID
    ats_score: int
    feedback: dict[str, Any]
    extracted_data: dict[str, Any]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ResumeResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    file_name: str
    file_url: str
    file_size: int
    created_at: datetime
    analysis: Optional[ResumeAnalysisResponse] = None
    skills: List[SkillSchema] = []
    education: List[EducationSchema] = []
    experience: List[ExperienceSchema] = []
    certifications: List[CertificationSchema] = []
    model_config = ConfigDict(from_attributes=True)
