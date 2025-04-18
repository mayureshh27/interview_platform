from deepface import DeepFace
import numpy as np
import cv2
import asyncio
import time
from typing import Dict, Any, List, Tuple
import logging
from app.core.config import settings
import tempfile
import os

logger = logging.getLogger(__name__)

class FacialAnalysisService:
    def __init__(self):
        self.model_name = settings.DEEPFACE_MODEL
        self.reference_image = None
        self.analysis_results = {
            "emotion_data": [],
            "face_match_scores": [],
            "liveness_scores": [],
            "has_spoofing_detected": False
        }
        self.last_processed_time = 0
        self.interval = settings.SPOOFING_DETECTION_INTERVAL
    
    def set_reference_image(self, image):
        """Set the reference image for comparison"""
        self.reference_image = image
        # Pre-process the reference image
        try:
            # Extract face from the reference image
            detected_face = DeepFace.extract_faces(
                img_path=self.reference_image,
                detector_backend='opencv'
            )
            if detected_face:
                logger.info("Reference image processed successfully")
                return True
            logger.error("No face detected in reference image")
            return False
        except Exception as e:
            logger.error(f"Error processing reference image: {e}")
            return False
    
    async def process_frame(self, frame) -> Dict[str, Any]:
        """Process a video frame for facial analysis"""
        current_time = time.time()
        
        # Only process frames at the defined interval
        if current_time - self.last_processed_time < self.interval:
            return None
        
        self.last_processed_time = current_time
        
        if self.reference_image is None:
            logger.warning("No reference image set for comparison")
            return None
        
        try:
            # Convert frame to numpy array if it's not already
            if not isinstance(frame, np.ndarray):
                frame = np.array(frame)
            
            # Save frame to temporary file for DeepFace
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp:
                temp_path = temp.name
                cv2.imwrite(temp_path, frame)
            
            # Verify face match with reference image
            verification = DeepFace.verify(
                img1_path=self.reference_image,
                img2_path=temp_path,
                model_name=self.model_name,
                detector_backend='opencv'
            )
            
            # Analyze emotions
            analysis = DeepFace.analyze(
                img_path=temp_path,
                actions=['emotion', 'age', 'gender'],
                detector_backend='opencv',
                silent=True
            )
            
            # Check for spoofing (basic implementation)
            liveness_score = self._check_liveness(frame)
            
            # Add results to history
            result = {
                'timestamp': current_time,
                'face_match': {
                    'verified': verification['verified'],
                    'distance': verification['distance'],
                    'threshold': verification['threshold'],
                },
                'emotion': analysis[0]['emotion'],
                'liveness_score': liveness_score,
                'spoofing_detected': liveness_score < 0.7  # Threshold for spoofing detection
            }
            
            # Update analysis results
            self.analysis_results['emotion_data'].append({
                'timestamp': current_time,
                'emotions': analysis[0]['emotion']
            })
            self.analysis_results['face_match_scores'].append({
                'timestamp': current_time, 
                'score': 1 - verification['distance']
            })
            self.analysis_results['liveness_scores'].append({
                'timestamp': current_time,
                'score': liveness_score
            })
            
            if result['spoofing_detected']:
                self.analysis_results['has_spoofing_detected'] = True
            
            # Clean up temp file
            os.unlink(temp_path)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing frame: {e}")
            return None
    
    def _check_liveness(self, frame) -> float:
        """
        Check if the face is real or spoofed
        This is a simplified implementation - in production, use a dedicated anti-spoofing model
        """
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)
            
            if len(faces) == 0:
                return 0.0  # No face detected
            
            # Get the first face
            (x, y, w, h) = faces[0]
            roi = gray[y:y+h, x:x+w]
            
            # Simple texture analysis for spoofing detection
            # In a real implementation, you would use a dedicated anti-spoofing model
            lbp = self._compute_local_binary_pattern(roi)
            var = np.var(lbp)
            
            # Normalize variance to 0-1 range (higher variance suggests real face)
            liveness_score = min(1.0, max(0.0, var / 5000))
            
            return liveness_score
            
        except Exception as e:
            logger.error(f"Error in liveness check: {e}")
            return 0.5  # Default to uncertain
    
    def _compute_local_binary_pattern(self, image):
        """Simple LBP implementation for texture analysis"""
        rows, cols = image.shape
        lbp = np.zeros_like(image)
        
        for i in range(1, rows-1):
            for j in range(1, cols-1):
                center = image[i, j]
                code = 0
                
                code |= (image[i-1, j-1] >= center) << 7
                code |= (image[i-1, j] >= center) << 6
                code |= (image[i-1, j+1] >= center) << 5
                code |= (image[i, j+1] >= center) << 4
                code |= (image[i+1, j+1] >= center) << 3
                code |= (image[i+1, j] >= center) << 2
                code |= (image[i+1, j-1] >= center) << 1
                code |= (image[i, j-1] >= center) << 0
                
                lbp[i, j] = code
                
        return lbp
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """Get summary of all analysis results"""
        if not self.analysis_results['face_match_scores']:
            return {
                "status": "no_data",
                "message": "No analysis data available"
            }
        
        # Calculate average scores
        avg_face_match = sum(item['score'] for item in self.analysis_results['face_match_scores']) / len(self.analysis_results['face_match_scores'])
        avg_liveness = sum(item['score'] for item in self.analysis_results['liveness_scores']) / len(self.analysis_results['liveness_scores'])
        
        # Get primary emotion
        emotions_count = {}
        for item in self.analysis_results['emotion_data']:
            max_emotion = max(item['emotions'].items(), key=lambda x: x[1])
            emotions_count[max_emotion[0]] = emotions_count.get(max_emotion[0], 0) + 1
        
        primary_emotion = max(emotions_count.items(), key=lambda x: x[1])[0] if emotions_count else "unknown"
        
        return {
            "face_match_score": avg_face_match,
            "liveness_score": avg_liveness,
            "has_spoofing_detected": self.analysis_results['has_spoofing_detected'],
            "primary_emotion": primary_emotion,
            "emotions_distribution": emotions_count,
            "analysis_count": len(self.analysis_results['face_match_scores']),
            "status": "completed"
        }