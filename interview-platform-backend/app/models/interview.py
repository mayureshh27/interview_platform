from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Enum, JSON
from sqlalchemy.orm import relationship
import enum
from app.models.base import BaseModel

class InterviewStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELED = "canceled"

class Interview(BaseModel):
    __tablename__ = "interviews"
    
    title = Column(String, nullable=False)
    description = Column(String)
    interviewer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    candidate_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    scheduled_start = Column(DateTime, nullable=False)
    scheduled_end = Column(DateTime, nullable=False)
    actual_start = Column(DateTime)
    actual_end = Column(DateTime)
    status = Column(Enum(InterviewStatus), default=InterviewStatus.SCHEDULED)
    
    interviewer = relationship("User", foreign_keys=[interviewer_id])
    candidate = relationship("User", foreign_keys=[candidate_id])
    analysis = relationship("Analysis", back_populates="interview", uselist=False)