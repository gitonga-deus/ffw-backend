from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from datetime import datetime
import json

from app.models.user_progress import UserProgress
from app.models.enrollment import Enrollment
from app.models.content import Content
from app.models.module import Module
from app.schemas.progress import (
    ProgressUpdateRequest,
    ContentProgressResponse,
    ModuleProgressResponse,
    OverallProgressResponse
)


class ProgressService:
    """Service for managing user progress."""

    def update_progress(
        self,
        db: Session,
        user_id: str,
        content_id: str,
        progress_data: ProgressUpdateRequest
    ) -> UserProgress:
        """
        Create or update user progress for a content item.
        Also updates enrollment progress percentage.
        """
        # Get or create progress record
        progress = db.query(UserProgress).filter(
            UserProgress.user_id == user_id,
            UserProgress.content_id == content_id
        ).first()

        if progress:
            # Update existing progress
            progress.is_completed = progress_data.is_completed
            progress.time_spent = progress_data.time_spent
            progress.last_position = progress_data.last_position
            progress.updated_at = datetime.utcnow()
            
            if progress_data.is_completed and not progress.completed_at:
                progress.completed_at = datetime.utcnow()
        else:
            # Create new progress record
            progress = UserProgress(
                user_id=user_id,
                content_id=content_id,
                is_completed=progress_data.is_completed,
                time_spent=progress_data.time_spent,
                last_position=progress_data.last_position,
                completed_at=datetime.utcnow() if progress_data.is_completed else None
            )
            db.add(progress)

        db.commit()
        db.refresh(progress)

        # Update enrollment progress
        self._update_enrollment_progress(db, user_id, content_id)

        return progress

    def _update_enrollment_progress(
        self,
        db: Session,
        user_id: str,
        last_accessed_content_id: str
    ) -> None:
        """
        Calculate and update overall progress percentage in enrollment.
        Includes exercises in the calculation.
        """
        from app.models.exercise import Exercise
        from app.models.exercise_submission import ExerciseSubmission
        
        # Get enrollment
        enrollment = db.query(Enrollment).filter(
            Enrollment.user_id == user_id
        ).first()

        if not enrollment:
            return

        # Get total published content count (includes all content types including exercises)
        total_content = db.query(func.count(Content.id)).filter(
            Content.is_published == True
        ).scalar()

        if total_content == 0:
            return

        # Get completed non-exercise content count for this user
        completed_regular_content = db.query(func.count(UserProgress.id)).filter(
            UserProgress.user_id == user_id,
            UserProgress.is_completed == True
        ).scalar()
        
        # Get completed exercise count for this user
        # An exercise is completed if there's a submission for it
        completed_exercises = db.query(func.count(ExerciseSubmission.id.distinct())).join(
            Exercise, ExerciseSubmission.exercise_id == Exercise.id
        ).join(
            Content, Exercise.content_id == Content.id
        ).filter(
            ExerciseSubmission.user_id == user_id,
            Content.is_published == True
        ).scalar()
        
        # Total completed content includes both regular content and exercises
        completed_content = completed_regular_content + completed_exercises

        # Calculate progress percentage
        progress_percentage = (completed_content / total_content) * 100

        # Update enrollment
        enrollment.progress_percentage = round(progress_percentage, 2)
        enrollment.last_accessed_module_id = db.query(Content.module_id).filter(
            Content.id == last_accessed_content_id
        ).scalar()
        enrollment.last_accessed_at = datetime.utcnow()

        db.commit()

    def get_overall_progress(
        self,
        db: Session,
        user_id: str
    ) -> OverallProgressResponse:
        """
        Get overall course progress for a user.
        Includes exercises in progress calculation.
        Optimized to avoid N+1 queries.
        """
        from sqlalchemy import case
        from app.models.exercise import Exercise
        from app.models.exercise_submission import ExerciseSubmission
        
        # Get enrollment
        enrollment = db.query(Enrollment).filter(
            Enrollment.user_id == user_id
        ).first()

        # Query for regular content progress (non-exercise)
        modules_with_progress = (
            db.query(
                Module,
                func.count(Content.id).label('content_count'),
                func.sum(
                    case(
                        (UserProgress.is_completed == True, 1),
                        else_=0
                    )
                ).label('completed_count')
            )
            .outerjoin(Content, (Content.module_id == Module.id) & (Content.is_published == True))
            .outerjoin(
                UserProgress,
                (UserProgress.content_id == Content.id) & (UserProgress.user_id == user_id)
            )
            .filter(Module.is_published == True)
            .group_by(Module.id)
            .order_by(Module.order_index)
            .all()
        )

        # Note: Exercise completions are already included in the main query above
        # UserProgress is the single source of truth for all content types including exercises
        # No need for separate exercise tracking

        module_progress_list = []
        total_content = 0
        completed_content = 0
        completed_modules = 0

        for module, module_total, module_completed in modules_with_progress:
            module_total = module_total or 0
            module_completed = module_completed or 0
            
            total_content += module_total
            completed_content += module_completed

            # Calculate module progress percentage
            module_progress_pct = (module_completed / module_total * 100) if module_total > 0 else 0

            if module_progress_pct == 100:
                completed_modules += 1

            module_progress_list.append(
                ModuleProgressResponse(
                    module_id=module.id,
                    module_title=module.title,
                    total_content=module_total,
                    completed_content=module_completed,
                    progress_percentage=round(module_progress_pct, 2)
                )
            )

        # Calculate overall progress
        overall_progress = (completed_content / total_content * 100) if total_content > 0 else 0

        # Get content breakdown by type
        from app.schemas.progress import ContentBreakdown, CompletedContentBreakdown
        
        content_breakdown_query = db.query(
            Content.content_type,
            func.count(Content.id).label('count')
        ).filter(
            Content.is_published == True
        ).group_by(Content.content_type).all()
        
        content_breakdown = ContentBreakdown()
        for content_type, count in content_breakdown_query:
            if content_type == 'video':
                content_breakdown.videos = count
            elif content_type == 'pdf':
                content_breakdown.pdfs = count
            elif content_type == 'rich_text':
                content_breakdown.rich_text = count
            elif content_type == 'exercise':
                content_breakdown.exercises = count
        
        # Get completed content breakdown by type
        completed_breakdown_query = db.query(
            Content.content_type,
            func.count(UserProgress.id).label('count')
        ).join(
            UserProgress, UserProgress.content_id == Content.id
        ).filter(
            UserProgress.user_id == user_id,
            UserProgress.is_completed == True,
            Content.is_published == True
        ).group_by(Content.content_type).all()
        
        completed_breakdown = CompletedContentBreakdown()
        for content_type, count in completed_breakdown_query:
            if content_type == 'video':
                completed_breakdown.videos = count
            elif content_type == 'pdf':
                completed_breakdown.pdfs = count
            elif content_type == 'rich_text':
                completed_breakdown.rich_text = count
            elif content_type == 'exercise':
                # Exercises are tracked in UserProgress (set by webhook)
                completed_breakdown.exercises = count

        # Get last accessed content details
        last_accessed_content = None
        if enrollment and enrollment.last_accessed_module_id:
            # Find the most recently accessed content in the last accessed module
            last_progress = db.query(UserProgress).join(
                Content, UserProgress.content_id == Content.id
            ).filter(
                UserProgress.user_id == user_id,
                Content.module_id == enrollment.last_accessed_module_id
            ).order_by(UserProgress.updated_at.desc()).first()
            
            if last_progress:
                content = db.query(Content).filter(
                    Content.id == last_progress.content_id
                ).first()
                if content:
                    last_accessed_content = {
                        "id": content.id,
                        "module_id": content.module_id,
                        "title": content.title,
                        "content_type": content.content_type
                    }

        return OverallProgressResponse(
            progress_percentage=round(overall_progress, 2),
            total_modules=len(module_progress_list),
            completed_modules=completed_modules,
            total_content=total_content,
            completed_content=completed_content,
            content_breakdown=content_breakdown,
            completed_breakdown=completed_breakdown,
            last_accessed_content_id=enrollment.last_accessed_module_id if enrollment else None,
            last_accessed_at=enrollment.last_accessed_at if enrollment else None,
            last_accessed_content=last_accessed_content,
            modules=module_progress_list
        )

    def get_content_progress(
        self,
        db: Session,
        user_id: str,
        content_id: str
    ) -> Optional[ContentProgressResponse]:
        """
        Get progress for a specific content item.
        """
        # Get content
        content = db.query(Content).filter(Content.id == content_id).first()
        if not content:
            return None

        # Get progress
        progress = db.query(UserProgress).filter(
            UserProgress.user_id == user_id,
            UserProgress.content_id == content_id
        ).first()

        if not progress:
            # Return default progress
            return ContentProgressResponse(
                content_id=content.id,
                content_title=content.title,
                content_type=content.content_type,
                is_completed=False,
                time_spent=0,
                last_position=None,
                completed_at=None,
                updated_at=datetime.utcnow()
            )

        return ContentProgressResponse(
            content_id=content.id,
            content_title=content.title,
            content_type=content.content_type,
            is_completed=progress.is_completed,
            time_spent=progress.time_spent,
            last_position=progress.last_position,
            completed_at=progress.completed_at,
            updated_at=progress.updated_at
        )

    def get_module_progress(
        self,
        db: Session,
        user_id: str,
        module_id: str
    ) -> List[ContentProgressResponse]:
        """
        Get progress for all content items in a module.
        Returns a list of ContentProgressResponse objects ordered by content order_index.
        """
        # Query all published content items for the module ordered by order_index
        content_items = db.query(Content).filter(
            Content.module_id == module_id,
            Content.is_published == True
        ).order_by(Content.order_index).all()

        progress_list = []

        # For each content item, get existing progress or create default response
        for content in content_items:
            progress = db.query(UserProgress).filter(
                UserProgress.user_id == user_id,
                UserProgress.content_id == content.id
            ).first()

            if progress:
                # Use existing progress
                progress_list.append(
                    ContentProgressResponse(
                        content_id=content.id,
                        content_title=content.title,
                        content_type=content.content_type,
                        is_completed=progress.is_completed,
                        time_spent=progress.time_spent,
                        last_position=progress.last_position,
                        completed_at=progress.completed_at,
                        updated_at=progress.updated_at
                    )
                )
            else:
                # Create default response for content without progress
                progress_list.append(
                    ContentProgressResponse(
                        content_id=content.id,
                        content_title=content.title,
                        content_type=content.content_type,
                        is_completed=False,
                        time_spent=0,
                        last_position=None,
                        completed_at=None,
                        updated_at=datetime.utcnow()
                    )
                )

        return progress_list

    # Old exercise response method - removed as part of 123FormBuilder integration
    # def submit_exercise_response(
    #     self,
    #     db: Session,
    #     user_id: str,
    #     exercise_data: ExerciseResponseRequest
    # ) -> ExerciseResponse:
    #     """
    #     Submit or update exercise response.
    #     """
    #     # This method was for the old exercise system that has been replaced

    def check_course_completion(
        self,
        db: Session,
        user_id: str
    ) -> bool:
        """
        Check if user has completed all required content including exercises.
        Returns True if course is completed.
        """
        from app.models.exercise import Exercise
        from app.models.exercise_submission import ExerciseSubmission
        
        # Get total published content count (includes all content types including exercises)
        total_content = db.query(func.count(Content.id)).filter(
            Content.is_published == True
        ).scalar()

        if total_content == 0:
            return False

        # Get completed content count for this user (includes all content types including exercises)
        # UserProgress is the single source of truth for all content completion
        completed_content = db.query(func.count(UserProgress.id)).join(
            Content, UserProgress.content_id == Content.id
        ).filter(
            UserProgress.user_id == user_id,
            UserProgress.is_completed == True,
            Content.is_published == True
        ).scalar()

        return completed_content >= total_content

    def check_module_completion(
        self,
        db: Session,
        user_id: str,
        module_id: str
    ) -> bool:
        """
        Check if user has completed all content in a module including exercises.
        Returns True if module is completed.
        
        UserProgress is the single source of truth for all content types.
        """
        # Get total published content count in this module
        total_content = db.query(func.count(Content.id)).filter(
            Content.module_id == module_id,
            Content.is_published == True
        ).scalar()

        if total_content == 0:
            return False

        # Get completed content count for this user in this module (includes all content types)
        # UserProgress is the single source of truth
        completed_content = db.query(func.count(UserProgress.id)).join(
            Content, UserProgress.content_id == Content.id
        ).filter(
            UserProgress.user_id == user_id,
            UserProgress.is_completed == True,
            Content.module_id == module_id,
            Content.is_published == True
        ).scalar()

        return completed_content >= total_content

    def mark_course_completed(
        self,
        db: Session,
        user_id: str
    ) -> None:
        """
        Mark course as completed in enrollment.
        """
        enrollment = db.query(Enrollment).filter(
            Enrollment.user_id == user_id
        ).first()

        if enrollment and not enrollment.completed_at:
            enrollment.completed_at = datetime.utcnow()
            enrollment.progress_percentage = 100.00
            db.commit()
    
    def recalculate_all_enrollments(
        self,
        db: Session
    ) -> int:
        """
        Recalculate progress for all enrollments.
        This should be called when content is added, removed, or published/unpublished.
        
        Returns:
            Number of enrollments updated
        """
        from app.models.user import User
        
        # Get all enrolled users
        enrolled_users = db.query(User).filter(User.is_enrolled == True).all()
        
        updated_count = 0
        
        for user in enrolled_users:
            enrollment = db.query(Enrollment).filter(
                Enrollment.user_id == user.id
            ).first()
            
            if not enrollment:
                continue
            
            # Get total published content count
            total_content = db.query(func.count(Content.id)).filter(
                Content.is_published == True
            ).scalar()
            
            if total_content == 0:
                continue
            
            # Get completed content count for this user
            completed_content = db.query(func.count(UserProgress.id)).join(
                Content, UserProgress.content_id == Content.id
            ).filter(
                UserProgress.user_id == user.id,
                UserProgress.is_completed == True,
                Content.is_published == True
            ).scalar()
            
            # Calculate new progress percentage
            new_progress = (completed_content / total_content) * 100
            
            # Update enrollment
            old_progress = enrollment.progress_percentage
            enrollment.progress_percentage = round(new_progress, 2)
            
            # Check if course is still completed
            if new_progress < 100 and enrollment.completed_at:
                # Course was completed but now has new content - reset completion
                enrollment.completed_at = None
                updated_count += 1
            elif new_progress >= 100 and not enrollment.completed_at:
                # Course is now completed
                enrollment.completed_at = datetime.utcnow()
                updated_count += 1
            elif old_progress != round(new_progress, 2):
                # Progress changed but completion status didn't
                updated_count += 1
        
        db.commit()
        return updated_count
    
    def can_access_content(
        self,
        db: Session,
        user_id: str,
        content_id: str
    ) -> tuple[bool, Optional[str]]:
        """
        Check if user can access a content item based on sequential completion.
        Returns (can_access, reason_if_blocked).
        
        Rules:
        - First content in first module is always accessible
        - To access any other content, the previous content must be completed
        - Previous content is determined by order_index within the same module,
          or the last content of the previous module
        """
        # Get the requested content with its module
        content = db.query(Content).filter(Content.id == content_id).first()
        if not content:
            return False, "Content not found"
        
        # Get the module
        module = db.query(Module).filter(Module.id == content.module_id).first()
        if not module:
            return False, "Module not found"
        
        # Check if this is the first content in the first module
        first_module = db.query(Module).filter(
            Module.course_id == module.course_id
        ).order_by(Module.order_index).first()
        
        if module.id == first_module.id and content.order_index == 0:
            # First content is always accessible
            return True, None
        
        # Check if there's a previous content in the same module
        if content.order_index > 0:
            # Get previous content in the same module
            previous_content = db.query(Content).filter(
                Content.module_id == content.module_id,
                Content.order_index == content.order_index - 1,
                Content.is_published == True
            ).first()
            
            if previous_content:
                # Check if previous content is completed
                previous_progress = db.query(UserProgress).filter(
                    UserProgress.user_id == user_id,
                    UserProgress.content_id == previous_content.id,
                    UserProgress.is_completed == True
                ).first()
                
                if not previous_progress:
                    return False, f"You must complete '{previous_content.title}' first"
                
                return True, None
        
        # This is the first content in a module (but not the first module)
        # Check if the previous module is completed
        previous_module = db.query(Module).filter(
            Module.course_id == module.course_id,
            Module.order_index == module.order_index - 1,
            Module.is_published == True
        ).first()
        
        if previous_module:
            # Get the last content of the previous module
            last_content_of_previous_module = db.query(Content).filter(
                Content.module_id == previous_module.id,
                Content.is_published == True
            ).order_by(Content.order_index.desc()).first()
            
            if last_content_of_previous_module:
                # Check if it's completed
                last_content_progress = db.query(UserProgress).filter(
                    UserProgress.user_id == user_id,
                    UserProgress.content_id == last_content_of_previous_module.id,
                    UserProgress.is_completed == True
                ).first()
                
                if not last_content_progress:
                    return False, f"You must complete the previous module '{previous_module.title}' first"
        
        return True, None


# Create singleton instance
progress_service = ProgressService()
