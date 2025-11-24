from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from datetime import datetime
import json
import re
import uuid

from app.models.exercise import Exercise
from app.models.exercise_submission import ExerciseSubmission
from app.models.user import User


class ExerciseService:
    """Service for managing exercises and submissions."""

    def validate_embed_code(self, embed_code: str) -> bool:
        """
        Validate that embed code is from 123FormBuilder.
        
        Checks for:
        - 123FormBuilder domain presence
        - Valid HTML structure (iframe or script tag)
        
        Args:
            embed_code: The embed code to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not embed_code or not isinstance(embed_code, str):
            return False
        
        # Check for 123FormBuilder domain
        if "123formbuilder.com" not in embed_code.lower():
            return False
        
        # Check for valid HTML structure (iframe or script tag)
        has_iframe = bool(re.search(r'<iframe[^>]*>.*?</iframe>', embed_code, re.IGNORECASE | re.DOTALL))
        has_script = bool(re.search(r'<script[^>]*>.*?</script>', embed_code, re.IGNORECASE | re.DOTALL))
        
        return has_iframe or has_script

    def extract_form_id_from_embed(self, embed_code: str) -> Optional[str]:
        """
        Extract form ID from 123FormBuilder embed code.
        
        Handles various embed code formats:
        - iframe src with form ID in URL
        - script tag with form ID in data attribute or URL
        
        Args:
            embed_code: The embed code to parse
            
        Returns:
            Form ID string if found, None otherwise
        """
        if not embed_code:
            return None
        
        # Only extract from 123FormBuilder domains
        if "123formbuilder.com" not in embed_code.lower():
            return None
        
        # Pattern 1: Look for form ID in iframe src
        # Example: src="https://www.123formbuilder.com/form-12345/..."
        iframe_pattern = r'<iframe[^>]*src=["\']([^"\']*123formbuilder\.com[^"\']*)["\']'
        iframe_match = re.search(iframe_pattern, embed_code, re.IGNORECASE)
        
        if iframe_match:
            src_url = iframe_match.group(1)
            # Extract form ID from URL patterns like:
            # - /my-contact-form-6238706.html
            # - /form-12345/
            # - /form/12345
            # - ?form=12345
            form_id_patterns = [
                r'/my-contact-form-(\d+)\.html',  # Matches /my-contact-form-6238706.html
                r'/form-(\d+)',
                r'/form/(\d+)',
                r'[?&]form=(\d+)',
                r'/my-form/(\d+)',
            ]
            
            for pattern in form_id_patterns:
                match = re.search(pattern, src_url)
                if match:
                    return match.group(1)
        
        # Pattern 2: Look for form ID in script tag
        # Example: data-form-id="12345" or similar
        script_pattern = r'data-form-id=["\'](\d+)["\']'
        script_match = re.search(script_pattern, embed_code, re.IGNORECASE)
        
        if script_match:
            return script_match.group(1)
        
        # Pattern 3: Look for form ID in script src URL
        script_src_pattern = r'<script[^>]*src=["\']([^"\']*123formbuilder\.com[^"\']*)["\']'
        script_src_match = re.search(script_src_pattern, embed_code, re.IGNORECASE)
        
        if script_src_match:
            src_url = script_src_match.group(1)
            form_id_patterns = [
                r'/(\d+)\.js',  # Matches /6236478.js format
                r'/embed/(\d+)',  # Matches /embed/6236478 format
                r'/form-(\d+)',
                r'/form/(\d+)',
                r'[?&]form=(\d+)',
            ]
            
            for pattern in form_id_patterns:
                match = re.search(pattern, src_url)
                if match:
                    return match.group(1)
        
        return None

    def create_exercise(
        self,
        db: Session,
        content_id: str,
        embed_code: str,
        form_title: str,
        allow_multiple_submissions: bool = False
    ) -> Exercise:
        """
        Create a new exercise with 123FormBuilder embed code.
        
        Args:
            db: Database session
            content_id: ID of the content item
            embed_code: 123FormBuilder embed code
            form_title: Title of the form
            allow_multiple_submissions: Whether to allow multiple submissions
            
        Returns:
            Created Exercise object
            
        Raises:
            ValueError: If embed code is invalid or form ID cannot be extracted
        """
        # Validate embed code
        if not self.validate_embed_code(embed_code):
            raise ValueError("Invalid 123FormBuilder embed code. Please ensure the embed code is from 123FormBuilder.")
        
        # Extract form ID
        form_id = self.extract_form_id_from_embed(embed_code)
        if not form_id:
            raise ValueError("Could not extract form ID from embed code. Please ensure you copied the complete embed code.")
        
        # Create exercise
        exercise = Exercise(
            id=str(uuid.uuid4()),
            content_id=content_id,
            form_id=form_id,
            embed_code=embed_code,
            form_title=form_title,
            allow_multiple_submissions=allow_multiple_submissions,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(exercise)
        db.commit()
        db.refresh(exercise)
        
        return exercise

    def get_exercise_by_content_id(
        self,
        db: Session,
        content_id: str
    ) -> Optional[Exercise]:
        """
        Get exercise by content ID.
        
        Args:
            db: Database session
            content_id: ID of the content item
            
        Returns:
            Exercise object if found, None otherwise
        """
        return db.query(Exercise).filter(
            Exercise.content_id == content_id
        ).first()

    def update_exercise_embed(
        self,
        db: Session,
        exercise_id: str,
        embed_code: str,
        form_title: Optional[str] = None
    ) -> Exercise:
        """
        Update exercise embed code.
        
        Args:
            db: Database session
            exercise_id: ID of the exercise
            embed_code: New embed code
            form_title: Optional new form title
            
        Returns:
            Updated Exercise object
            
        Raises:
            ValueError: If exercise not found or embed code is invalid
        """
        exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
        if not exercise:
            raise ValueError(f"Exercise with ID {exercise_id} not found")
        
        # Validate new embed code
        if not self.validate_embed_code(embed_code):
            raise ValueError("Invalid 123FormBuilder embed code. Please ensure the embed code is from 123FormBuilder.")
        
        # Extract new form ID
        new_form_id = self.extract_form_id_from_embed(embed_code)
        if not new_form_id:
            raise ValueError("Could not extract form ID from embed code. Please ensure you copied the complete embed code.")
        
        # Update exercise
        exercise.embed_code = embed_code
        exercise.form_id = new_form_id
        if form_title:
            exercise.form_title = form_title
        exercise.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(exercise)
        
        return exercise

    def delete_exercise(
        self,
        db: Session,
        exercise_id: str
    ) -> bool:
        """
        Delete an exercise.
        
        Note: Submissions will be cascade deleted due to foreign key constraint.
        
        Args:
            db: Database session
            exercise_id: ID of the exercise to delete
            
        Returns:
            True if deleted, False if not found
        """
        exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
        if not exercise:
            return False
        
        db.delete(exercise)
        db.commit()
        
        return True

    def record_submission(
        self,
        db: Session,
        exercise_id: str,
        user_id: str,
        form_submission_id: str,
        submission_data: dict,
        submitted_at: datetime
    ) -> ExerciseSubmission:
        """
        Record a form submission from webhook.
        
        Args:
            db: Database session
            exercise_id: ID of the exercise
            user_id: ID of the user who submitted
            form_submission_id: 123FormBuilder submission ID
            submission_data: Form response data
            submitted_at: When the form was submitted
            
        Returns:
            Created or updated ExerciseSubmission object
            
        Raises:
            ValueError: If exercise not found or user not found
        """
        # Verify exercise exists
        exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
        if not exercise:
            raise ValueError(f"Exercise with ID {exercise_id} not found")
        
        # Verify user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        # Convert submission data to JSON string
        submission_json = json.dumps(submission_data)
        
        # Check if submission already exists
        existing_submission = db.query(ExerciseSubmission).filter(
            ExerciseSubmission.exercise_id == exercise_id,
            ExerciseSubmission.user_id == user_id
        ).first()
        
        if existing_submission:
            # Update existing submission if multiple submissions allowed
            if exercise.allow_multiple_submissions:
                existing_submission.form_submission_id = form_submission_id
                existing_submission.submission_data = submission_json
                existing_submission.submitted_at = submitted_at
                existing_submission.webhook_received_at = datetime.utcnow()
                
                db.commit()
                db.refresh(existing_submission)
                
                return existing_submission
            else:
                # Return existing submission without updating
                return existing_submission
        
        # Create new submission
        submission = ExerciseSubmission(
            id=str(uuid.uuid4()),
            exercise_id=exercise_id,
            user_id=user_id,
            form_submission_id=form_submission_id,
            submission_data=submission_json,
            submitted_at=submitted_at,
            webhook_received_at=datetime.utcnow()
        )
        
        db.add(submission)
        db.commit()
        db.refresh(submission)
        
        return submission

    def get_user_submission(
        self,
        db: Session,
        exercise_id: str,
        user_id: str
    ) -> Optional[ExerciseSubmission]:
        """
        Get a user's submission for an exercise.
        
        Args:
            db: Database session
            exercise_id: ID of the exercise
            user_id: ID of the user
            
        Returns:
            ExerciseSubmission object if found, None otherwise
        """
        return db.query(ExerciseSubmission).filter(
            ExerciseSubmission.exercise_id == exercise_id,
            ExerciseSubmission.user_id == user_id
        ).first()

    def get_all_submissions(
        self,
        db: Session,
        exercise_id: str
    ) -> List[ExerciseSubmission]:
        """
        Get all submissions for an exercise.
        
        Args:
            db: Database session
            exercise_id: ID of the exercise
            
        Returns:
            List of ExerciseSubmission objects
        """
        return db.query(ExerciseSubmission).filter(
            ExerciseSubmission.exercise_id == exercise_id
        ).order_by(ExerciseSubmission.submitted_at.desc()).all()

    def check_completion_status(
        self,
        db: Session,
        exercise_id: str,
        user_id: str
    ) -> bool:
        """
        Check if a user has completed an exercise.
        
        Args:
            db: Database session
            exercise_id: ID of the exercise
            user_id: ID of the user
            
        Returns:
            True if user has submitted the exercise, False otherwise
        """
        submission = self.get_user_submission(db, exercise_id, user_id)
        return submission is not None


# Create singleton instance
exercise_service = ExerciseService()
