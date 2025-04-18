from sqlalchemy import Column, Integer, ForeignKey, Float, JSON, String, Boolean
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class Analysis(BaseModel):
    __tablename__ = "analyses"
    
    interview_id = Column(Integer, ForeignKey("interviews.id"), nullable=False)
    face_match_score = Column(Float)  # Similarity score 0-1
    emotion_data = Column(JSON)  # Emotions detected over time
    liveness_score = Column(Float)  # Anti-spoofing score 0-1
    has_spoofing_detected = Column(Boolean, default=False)
    recording_path = Column(String)  # Path to saved recording
    summary = Column(JSON)  # Summary of analysis results
    
    interview = relationship("Interview", back_populates="analysis")