from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Any, List, Optional
from app.models.interview import InterviewStatus

class InterviewBase(BaseModel):
    title: str
    description: Optional[str] = None
    interviewer_id: int
    candidate_id: int
    scheduled_start: datetime
    scheduled_end: datetime

class InterviewCreate(InterviewBase):
    pass

class InterviewUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    status: Optional[InterviewStatus] = None

class InterviewResponse(InterviewBase):
    id: int
    status: InterviewStatus
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class AnalysisSummary(BaseModel):
    face_match_score: Optional[float] = None
    liveness_score: Optional[float] = None
    has_spoofing_detected: bool = False
    primary_emotion: Optional[str] = None
    emotions_distribution: Optional[Dict[str, int]] = None
    analysis_count: int = 0
    status: str

class AnalysisResponse(BaseModel):
    id: int
    interview_id: int
    face_match_score: Optional[float] = None
    emotion_data: Optional[Dict[str, Any]] = None
    liveness_score: Optional[float] = None
    has_spoofing_detected: bool = False
    recording_path: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True