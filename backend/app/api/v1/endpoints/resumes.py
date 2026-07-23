import uuid
from typing import List, Any, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, status, Response
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pathlib import Path
import io

from app.core.db import get_db
from app.core.exceptions import NotFoundException, ForbiddenException, BadRequestException
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.resume import ResumeResponse, RescoreRequest
from app.repositories.resume import ResumeRepository
from app.services.storage import StorageService
from app.services.parser import ParserService
from app.services.scoring import ScoringService
from app.services.recommendation import RecommendationService

router = APIRouter()

@router.post("/upload", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    target_job_description: Optional[str] = Form(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Upload a resume (PDF or DOCX), parse it, calculate ATS scores, and save it to the database."""
    filename = file.filename or "resume.pdf"
    ext = Path(filename).suffix.lower()
    if ext not in [".pdf", ".docx", ".doc"]:
        raise BadRequestException(message="Unsupported file type. Please upload a PDF or DOCX file.")
        
    try:
        content = await file.read()
    except Exception:
        raise BadRequestException(message="Failed to read uploaded file.")
        
    if not content:
        raise BadRequestException(message="Uploaded file is empty.")

    storage_service = StorageService()
    file_url, file_size = await storage_service.save_file(content, filename)

    try:
        parser_service = ParserService()
        parsed_data = await parser_service.parse_resume(content, filename)
        
        scoring_service = ScoringService()
        scored_result = scoring_service.calculate_ats_score(
            parsed_data=parsed_data,
            target_job_description=target_job_description
        )
        
        resume_repo = ResumeRepository(db)
        resume = await resume_repo.create_resume_hierarchy(
            user_id=current_user.id,
            file_name=filename,
            file_url=file_url,
            file_size=file_size,
            parsed_data=parsed_data,
            scored_result=scored_result
        )
        
        fully_loaded = await resume_repo.get_by_id_fully_loaded(resume.id)
        return fully_loaded
        
    except Exception as e:
        await storage_service.delete_file(file_url)
        raise BadRequestException(message=f"Resume processing failed: {str(e)}")


@router.get("/my-resumes", response_model=List[ResumeResponse])
async def get_my_resumes(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Retrieve all resumes uploaded by the authenticated user."""
    resume_repo = ResumeRepository(db)
    resumes = await resume_repo.get_all_user_resumes(user_id=current_user.id)
    return resumes


@router.get("/{resume_id}", response_model=ResumeResponse)
async def get_resume(
    resume_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Retrieve full parsed details, layout logs, and ATS score for a specific resume."""
    resume_repo = ResumeRepository(db)
    resume = await resume_repo.get_by_id_fully_loaded(id=resume_id)
    
    if not resume:
        raise NotFoundException(message="Resume not found.")
        
    if resume.user_id != current_user.id:
        raise ForbiddenException(message="You do not have access to this resume.")
        
    return resume


@router.delete("/{resume_id}", status_code=status.HTTP_200_OK)
async def delete_resume(
    resume_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Soft delete a resume and purge its raw file from storage."""
    resume_repo = ResumeRepository(db)
    resume = await resume_repo.get(id=resume_id)
    
    if not resume:
        raise NotFoundException(message="Resume not found.")
        
    if resume.user_id != current_user.id:
        raise ForbiddenException(message="You do not have access to this resume.")
        
    storage_service = StorageService()
    await storage_service.delete_file(resume.file_url)
    
    await resume_repo.soft_delete(id=resume_id)
    return {"success": True, "message": "Resume deleted successfully."}


@router.post("/{resume_id}/rescore", response_model=ResumeResponse)
async def rescore_resume(
    resume_id: uuid.UUID,
    payload: RescoreRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Re-evaluate ATS score for an existing resume with a new target job description."""
    resume_repo = ResumeRepository(db)
    resume = await resume_repo.get_by_id_fully_loaded(id=resume_id)
    
    if not resume:
        raise NotFoundException(message="Resume not found.")
        
    if resume.user_id != current_user.id:
        raise ForbiddenException(message="You do not have access to this resume.")

    parsed_data = {}
    if resume.analysis and resume.analysis.extracted_data:
        parsed_data = dict(resume.analysis.extracted_data)
        parsed_data["skills"] = [{"name": s.name, "category": s.category} for s in resume.skills]
    else:
        parsed_data = {
            "name": current_user.full_name or "Resume Candidate",
            "skills": [{"name": s.name, "category": s.category} for s in resume.skills],
            "raw_text": " ".join([s.name for s in resume.skills])
        }

    scoring_service = ScoringService()
    scored_result = scoring_service.calculate_ats_score(
        parsed_data=parsed_data,
        target_job_description=payload.target_job_description
    )
    
    if resume.analysis:
        resume.analysis.ats_score = scored_result["ats_score"]
        resume.analysis.feedback = scored_result["feedback"]
        await db.commit()

    updated = await resume_repo.get_by_id_fully_loaded(id=resume_id)
    return updated


@router.get("/{resume_id}/report")
async def download_resume_report(
    resume_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Download a compiled PDF evaluation report for a resume analysis."""
    resume_repo = ResumeRepository(db)
    resume = await resume_repo.get_by_id_fully_loaded(id=resume_id)
    
    if not resume or not resume.analysis:
        raise NotFoundException(message="Resume analysis not found.")
        
    if resume.user_id != current_user.id:
        raise ForbiddenException(message="You do not have access to this report.")
        
    scoring_service = ScoringService()
    candidate_name = resume.analysis.extracted_data.get("name") or current_user.full_name or "Candidate"
    
    pdf_bytes = scoring_service.generate_pdf_report(
        candidate_name=candidate_name,
        ats_score=resume.analysis.ats_score,
        feedback=resume.analysis.feedback
    )
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=NaziranGPT_Report_{resume_id}.pdf"
        }
    )


@router.get("/download/{filename}")
async def download_uploaded_file(
    filename: str,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Retrieve raw uploaded resume file directly from storage."""
    file_path = Path("uploads") / filename
    if not file_path.exists():
        raise NotFoundException(message="File not found in storage.")
    return FileResponse(
        path=str(file_path),
        media_type="application/octet-stream",
        filename=filename
    )


@router.get("/{resume_id}/recommendations")
async def get_resume_recommendations(
    resume_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Generate career development recommendations, roadmap timeline, and skill gap metrics."""
    resume_repo = ResumeRepository(db)
    resume = await resume_repo.get_by_id_fully_loaded(id=resume_id)
    
    if not resume:
        raise NotFoundException(message="Resume not found.")
        
    if resume.user_id != current_user.id:
        raise ForbiddenException(message="You do not have access to this resume.")

    # Extract skill names
    skills = [skill.name for skill in resume.skills]
    
    recommendation_service = RecommendationService()
    recommendations = await recommendation_service.get_recommendations(skills)
    return recommendations
