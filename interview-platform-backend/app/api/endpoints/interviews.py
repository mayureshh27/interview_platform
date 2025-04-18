from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import Any, List, Optional
from datetime import datetime

from app.db.session import get_db
from app.schemas.interview import (
    InterviewCreate, InterviewUpdate, InterviewResponse, 
    AnalysisResponse, AnalysisSummary
)
from app.services.webrtc import WebRTCService

from app.models.interview import Interview, InterviewStatus
from app.models.analysis import Analysis
from app.models.user import User

router = APIRouter()

@router.post("/", response_model=InterviewResponse)
async def create_interview(
    interview: InterviewCreate,
    db: Session = Depends(get_db)
) -> Any:
    """Create a new interview"""
    # Check if interviewer exists
    interviewer = db.query(User).filter(User.id == interview.interviewer_id).first()
    if not interviewer:
        raise HTTPException(status_code=404, detail="Interviewer not found")
    
    # Check if candidate exists
    candidate = db.query(User).filter(User.id == interview.candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    # Create interview instance
    db_interview = Interview(
        title=interview.title,
        description=interview.description,
        interviewer_id=interview.interviewer_id,
        candidate_id=interview.candidate_id,
        scheduled_start=interview.scheduled_start,
        scheduled_end=interview.scheduled_end,
        status=InterviewStatus.SCHEDULED
    )
    
    # Add to database
    db.add(db_interview)
    db.commit()
    db.refresh(db_interview)
    
    return db_interview

@router.get("/", response_model=List[InterviewResponse])
async def list_interviews(
    skip: int = 0,
    limit: int = 100,
    status: Optional[InterviewStatus] = None,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db)
) -> Any:
    """List interviews with optional filters"""
    query = db.query(Interview)
    
    # Apply filters
    if status:
        query = query.filter(Interview.status == status)
    
    if user_id:
        query = query.filter(
            (Interview.interviewer_id == user_id) | (Interview.candidate_id == user_id)
        )
    
    # Apply pagination
    interviews = query.offset(skip).limit(limit).all()
    return interviews

@router.get("/{interview_id}", response_model=InterviewResponse)
async def get_interview(
    interview_id: int,
    db: Session = Depends(get_db)
) -> Any:
    """Get interview by ID"""
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    return interview

@router.put("/{interview_id}", response_model=InterviewResponse)
async def update_interview(
    interview_id: int,
    interview_update: InterviewUpdate,
    db: Session = Depends(get_db)
) -> Any:
    """Update interview details"""
    db_interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not db_interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    # Update attributes
    update_data = interview_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_interview, field, value)
    
    db.commit()
    db.refresh(db_interview)
    
    return db_interview

@router.post("/{interview_id}/start", response_model=InterviewResponse)
async def start_interview(
    interview_id: int,
    db: Session = Depends(get_db)
) -> Any:
    """Start an interview"""
    db_interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not db_interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    if db_interview.status != InterviewStatus.SCHEDULED:
        raise HTTPException(status_code=400, detail="Interview is not in scheduled state")
    
    # Update interview status
    db_interview.status = InterviewStatus.IN_PROGRESS
    db_interview.actual_start = datetime.utcnow()
    
    # Create analysis record
    analysis = Analysis(interview_id=interview_id)
    db.add(analysis)
    
    db.commit()
    db.refresh(db_interview)
    
    return db_interview

@router.post("/{interview_id}/end", response_model=InterviewResponse)
async def end_interview(
    interview_id: int,
    db: Session = Depends(get_db)
) -> Any:
    """End an interview"""
    db_interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not db_interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    if db_interview.status != InterviewStatus.IN_PROGRESS:
        raise HTTPException(status_code=400, detail="Interview is not in progress")
    
    # Update interview status
    db_interview.status = InterviewStatus.COMPLETED
    db_interview.actual_end = datetime.utcnow()
    
    db.commit()
    db.refresh(db_interview)
    
    return db_interview

@router.get("/{interview_id}/analysis", response_model=AnalysisResponse)
async def get_interview_analysis(
    interview_id: int,
    db: Session = Depends(get_db)
) -> Any:
    """Get interview analysis results"""
    # Check if interview exists
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    # Get analysis record
    analysis = db.query(Analysis).filter(Analysis.interview_id == interview_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return analysis