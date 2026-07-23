from __future__ import annotations
import uuid
from typing import List, Optional, Any
from sqlalchemy import String, Integer, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.base import UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin

class Resume(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "resumes"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    raw_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="resumes")
    analysis: Mapped[Optional["ResumeAnalysis"]] = relationship(
        "ResumeAnalysis", back_populates="resume", uselist=False, cascade="all, delete"
    )
    skills: Mapped[List["Skill"]] = relationship("Skill", back_populates="resume", cascade="all, delete")
    education: Mapped[List["Education"]] = relationship("Education", back_populates="resume", cascade="all, delete")
    experience: Mapped[List["Experience"]] = relationship("Experience", back_populates="resume", cascade="all, delete")
    certifications: Mapped[List["Certification"]] = relationship(
        "Certification", back_populates="resume", cascade="all, delete"
    )


class ResumeAnalysis(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "resume_analyses"

    resume_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False
    )
    ats_score: Mapped[int] = mapped_column(Integer, nullable=False)
    feedback: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    extracted_data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)

    # Relationships
    resume: Mapped["Resume"] = relationship("Resume", back_populates="analysis")


class Skill(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "skills"

    resume_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationships
    resume: Mapped["Resume"] = relationship("Resume", back_populates="skills")


class Education(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "education"

    resume_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    institution: Mapped[str] = mapped_column(String(255), nullable=False)
    degree: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    field_of_study: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    start_date: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    end_date: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    resume: Mapped["Resume"] = relationship("Resume", back_populates="education")


class Experience(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "experience"

    resume_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    company: Mapped[str] = mapped_column(String(255), nullable=False)
    position: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    start_date: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    end_date: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    resume: Mapped["Resume"] = relationship("Resume", back_populates="experience")


class Certification(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "certifications"

    resume_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    issuing_organization: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    issue_date: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    expiration_date: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Relationships
    resume: Mapped["Resume"] = relationship("Resume", back_populates="certifications")
