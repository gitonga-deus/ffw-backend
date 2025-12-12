"""
Progress Service - Rebuilt with improved architecture.

This service provides robust progress tracking with:
- Transaction-based updates for data consistency
- Optimized database queries with proper joins
- Sequential access validation
- Accurate progress calculations
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, case, and_
from typing import Optional, List, Tuple
from datetime import datetime
from decimal import Decimal

from app.models.user_progress import UserProgress
from app.models.enrollment import Enrollment
from app.models.content import Content
from app.models.module import Module
from app.schemas.progress import (
    ProgressUpdateRequest,
    ContentProgressResponse,
    ModuleProgressResponse,
    OverallProgressResponse,
    ContentBreakdown,
    CompletedContentBreakdown
)


class ProgressService:
    """
    Rebuilt progress service with improved reliability and performance.
    
    Key improvements:
    - All operations use database transactions
    - Optimized queries with joins to avoid N+1 problems
    - Clear separation of concerns
    - Comprehensive error handling
    """

    def update_progress(
        self,
        db: Session,
        user_id: str,
        content_id: str,
        progress_data: ProgressUpdateRequest
    ) -> UserProgress:
        """
        Create or update user progress for a content item.
        
        This method:
        1. Creates or updates the progress record
        2. Recalculates enrollment progress
        3. Uses a transaction to ensure consistency
        
        Args:
            db: Database session
            user_id: User ID
            content_id: Content ID
            progress_data: Progress update data
            
        Returns:
            Updated UserProgress record
            
        Raises:
            ValueError: If content doesn't exist or isn't published
        """
        try:
            # Verify content exists and is published
            content = db.query(Content).filter(
                Content.id == content_id,
                Content.is_published == True
            ).first()
            
            if not content:
                raise ValueError("Content not found or not published")
            
            # Get or create progress record
            progress = db.query(UserProgress).filter(
                UserProgress.user_id == user_id,
                UserProgress.content_id == content_id
            ).first()

            if progress:
                # Update existing progress
                progress.is_completed = progress_data.is_completed
                progress.updated_at = datetime.utcnow()
                
                # Set completed_at timestamp on first completion
                if progress_data.is_completed and not progress.completed_at:
                    progress.completed_at = datetime.utcnow()
            else:
                # Create new progress record
                progress = UserProgress(
                    user_id=user_id,
                    content_id=content_id,
                    is_completed=progress_data.is_completed,
                    time_spent=0,
                    last_position=None,
                    completed_at=datetime.utcnow() if progress_data.is_completed else None
                )
                db.add(progress)

            # Commit progress update
            db.commit()
            db.refresh(progress)

            # Recalculate enrollment progress on completion
            # For partial updates, we skip recalculation to improve performance
            # The enrollment progress is primarily based on completed content
            if progress_data.is_completed:
                self.recalculate_enrollment_progress(db, user_id)

            return progress
            
        except Exception as e:
            db.rollback()
            raise

    def get_overall_progress(
        self,
        db: Session,
        user_id: str
    ) -> OverallProgressResponse:
        """
        Get overall course progress for a user with optimized queries.
        
        Uses a single query with joins to fetch all module progress data,
        avoiding N+1 query problems.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            OverallProgressResponse with complete progress data
        """
        # Get enrollment
        enrollment = db.query(Enrollment).filter(
            Enrollment.user_id == user_id
        ).first()

        # Query for all modules with their content progress in a single query
        # This uses LEFT JOINs to include modules even if they have no content
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
            .outerjoin(
                Content,
                and_(
                    Content.module_id == Module.id,
                    Content.is_published == True
                )
            )
            .outerjoin(
                UserProgress,
                and_(
                    UserProgress.content_id == Content.id,
                    UserProgress.user_id == user_id
                )
            )
            .filter(Module.is_published == True)
            .group_by(Module.id)
            .order_by(Module.order_index)
            .all()
        )

        # Build module progress list
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
            module_progress_pct = (
                (module_completed / module_total * 100) if module_total > 0 else 0
            )

            if module_progress_pct == 100 and module_total > 0:
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
        overall_progress = (
            (completed_content / total_content * 100) if total_content > 0 else 0
        )

        # Get content breakdown by type
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
                completed_breakdown.exercises = count

        # Get last accessed content details
        last_accessed_content = None
        if enrollment and enrollment.last_accessed_module_id:
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

    def get_module_progress(
        self,
        db: Session,
        user_id: str,
        module_id: str
    ) -> List[ContentProgressResponse]:
        """
        Get progress for all content items in a module using batch queries.
        
        Uses a single query with a join to fetch all content and progress data,
        avoiding N+1 query problems.
        
        Args:
            db: Database session
            user_id: User ID
            module_id: Module ID
            
        Returns:
            List of ContentProgressResponse objects ordered by content order_index
        """
        # Single query to get all content with their progress
        content_with_progress = (
            db.query(Content, UserProgress)
            .outerjoin(
                UserProgress,
                and_(
                    UserProgress.content_id == Content.id,
                    UserProgress.user_id == user_id
                )
            )
            .filter(
                Content.module_id == module_id,
                Content.is_published == True
            )
            .order_by(Content.order_index)
            .all()
        )

        progress_list = []
        for content, progress in content_with_progress:
            if progress:
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
                # No progress record exists yet
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

    def get_content_progress(
        self,
        db: Session,
        user_id: str,
        content_id: str
    ) -> Optional[ContentProgressResponse]:
        """
        Get progress for a specific content item.
        
        Args:
            db: Database session
            user_id: User ID
            content_id: Content ID
            
        Returns:
            ContentProgressResponse or None if content doesn't exist
        """
        # Single query with join
        result = (
            db.query(Content, UserProgress)
            .outerjoin(
                UserProgress,
                and_(
                    UserProgress.content_id == Content.id,
                    UserProgress.user_id == user_id
                )
            )
            .filter(Content.id == content_id)
            .first()
        )

        if not result:
            return None

        content, progress = result

        if progress:
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
        else:
            # No progress record exists yet
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

    def can_access_content(
        self,
        db: Session,
        user_id: str,
        content_id: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if user can access a content item based on sequential completion rules.
        
        Rules:
        1. First content in first module is always accessible
        2. To access any other content, the previous content must be completed
        3. Previous content is determined by order_index within the same module
        4. If first content in a module, the last content of previous module must be completed
        5. Already completed content is always accessible (for review)
        
        Args:
            db: Database session
            user_id: User ID
            content_id: Content ID to check access for
            
        Returns:
            Tuple of (can_access: bool, reason_if_blocked: Optional[str])
        """
        # Get the requested content with its module in a single query
        result = (
            db.query(Content, Module)
            .join(Module, Content.module_id == Module.id)
            .filter(Content.id == content_id)
            .first()
        )
        
        if not result:
            return False, "Content not found"
        
        content, module = result
        
        # Check if content is published
        if not content.is_published:
            return False, "Content is not published"
        
        # Check if module is published
        if not module.is_published:
            return False, "Module is not published"
        
        # Rule 5: Already completed content is always accessible (for review)
        existing_progress = db.query(UserProgress).filter(
            UserProgress.user_id == user_id,
            UserProgress.content_id == content_id,
            UserProgress.is_completed == True
        ).first()
        
        if existing_progress:
            return True, None
        
        # Rule 1: First content in first module is always accessible
        first_module = db.query(Module).filter(
            Module.course_id == module.course_id,
            Module.is_published == True
        ).order_by(Module.order_index).first()
        
        if first_module and module.id == first_module.id and content.order_index == 0:
            return True, None
        
        # Rule 2 & 3: Check if there's a previous content in the same module
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
            else:
                # No previous content found (might be unpublished)
                # Allow access if this is effectively the first published content
                return True, None
        
        # Rule 4: This is the first content in a module (but not the first module)
        # Check if the previous module is completed
        if module.order_index > 0:
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
                else:
                    # Previous module has no published content, allow access
                    return True, None
            else:
                # No previous module found (might be unpublished)
                # Allow access if this is effectively the first published module
                return True, None
        
        return True, None

    def calculate_progress_percentage(
        self,
        completed_count: int,
        total_count: int
    ) -> float:
        """
        Calculate progress percentage from completed and total counts.
        
        Args:
            completed_count: Number of completed items
            total_count: Total number of items
            
        Returns:
            Progress percentage rounded to 2 decimal places (0.00 to 100.00)
        """
        if total_count == 0:
            return 0.0
        
        percentage = (completed_count / total_count) * 100
        return round(percentage, 2)

    def update_last_accessed(
        self,
        db: Session,
        user_id: str,
        module_id: str
    ) -> None:
        """
        Update the last accessed module for a user.
        
        This allows users to resume where they left off.
        
        Args:
            db: Database session
            user_id: User ID
            module_id: Module ID that was accessed
        """
        try:
            enrollment = db.query(Enrollment).filter(
                Enrollment.user_id == user_id
            ).first()

            if enrollment:
                enrollment.last_accessed_module_id = module_id
                enrollment.last_accessed_at = datetime.utcnow()
                db.commit()
                
        except Exception as e:
            db.rollback()
            raise

    def recalculate_enrollment_progress(
        self,
        db: Session,
        user_id: str
    ) -> None:
        """
        Recalculate and update enrollment progress percentage.
        
        This method:
        1. Counts total published content
        2. Counts completed content for the user
        3. Calculates progress percentage
        4. Updates enrollment record
        5. Uses a transaction to ensure consistency
        
        Args:
            db: Database session
            user_id: User ID
        """
        try:
            # Get enrollment
            enrollment = db.query(Enrollment).filter(
                Enrollment.user_id == user_id
            ).first()

            if not enrollment:
                return

            # Get total published content count
            total_content = db.query(func.count(Content.id)).filter(
                Content.is_published == True
            ).scalar()

            if total_content == 0:
                return

            # Get completed content count for this user
            completed_content = db.query(func.count(UserProgress.id)).join(
                Content, UserProgress.content_id == Content.id
            ).filter(
                UserProgress.user_id == user_id,
                UserProgress.is_completed == True,
                Content.is_published == True
            ).scalar()

            # Calculate progress percentage
            progress_percentage = self.calculate_progress_percentage(
                completed_content, total_content
            )

            # Update enrollment
            enrollment.progress_percentage = Decimal(str(progress_percentage))
            enrollment.last_accessed_at = datetime.utcnow()

            db.commit()
            
        except Exception as e:
            db.rollback()
            raise

    def check_course_completion(
        self,
        db: Session,
        user_id: str
    ) -> bool:
        """
        Check if user has completed all required content.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            True if all published content is completed, False otherwise
        """
        # Get total published content count
        total_content = db.query(func.count(Content.id)).filter(
            Content.is_published == True
        ).scalar()

        if total_content == 0:
            return False

        # Get completed content count for this user
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
        Check if user has completed all content in a module.
        
        Args:
            db: Database session
            user_id: User ID
            module_id: Module ID
            
        Returns:
            True if all published content in module is completed, False otherwise
        """
        # Get total published content count in this module
        total_content = db.query(func.count(Content.id)).filter(
            Content.module_id == module_id,
            Content.is_published == True
        ).scalar()

        if total_content == 0:
            return False

        # Get completed content count for this user in this module
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
        
        Uses atomic transaction to ensure consistency.
        
        Args:
            db: Database session
            user_id: User ID
        """
        try:
            enrollment = db.query(Enrollment).filter(
                Enrollment.user_id == user_id
            ).first()

            if enrollment and not enrollment.completed_at:
                enrollment.completed_at = datetime.utcnow()
                enrollment.progress_percentage = Decimal("100.00")
                db.commit()
                
        except Exception as e:
            db.rollback()
            raise

    def recalculate_all_enrollments(
        self,
        db: Session
    ) -> int:
        """
        Recalculate progress for all enrollments.
        
        This should be called when:
        - Content is added, removed, or published/unpublished
        - Course structure changes
        
        The method:
        1. Iterates through all enrollments
        2. Recalculates progress percentage for each
        3. Resets completion status if new content was added
        4. Marks as complete if all content is now finished
        
        Args:
            db: Database session
            
        Returns:
            Number of enrollments updated
        """
        try:
            # Get all enrollments
            enrollments = db.query(Enrollment).all()
            
            updated_count = 0
            
            # Get total published content count (same for all users)
            total_content = db.query(func.count(Content.id)).filter(
                Content.is_published == True
            ).scalar()
            
            if total_content == 0:
                return 0
            
            for enrollment in enrollments:
                # Get completed content count for this user
                completed_content = db.query(func.count(UserProgress.id)).join(
                    Content, UserProgress.content_id == Content.id
                ).filter(
                    UserProgress.user_id == enrollment.user_id,
                    UserProgress.is_completed == True,
                    Content.is_published == True
                ).scalar()
                
                # Calculate new progress percentage
                new_progress = self.calculate_progress_percentage(
                    completed_content, total_content
                )
                
                # Store old values for comparison
                old_progress = float(enrollment.progress_percentage) if enrollment.progress_percentage else 0.0
                was_completed = enrollment.completed_at is not None
                
                # Update progress percentage
                enrollment.progress_percentage = Decimal(str(new_progress))
                
                # Handle completion status changes
                if new_progress < 100 and was_completed:
                    # Course was completed but now has new content - reset completion
                    enrollment.completed_at = None
                    updated_count += 1
                elif new_progress >= 100 and not was_completed:
                    # Course is now completed
                    enrollment.completed_at = datetime.utcnow()
                    updated_count += 1
                elif abs(old_progress - new_progress) > 0.01:
                    # Progress changed but completion status didn't
                    updated_count += 1
            
            db.commit()
            return updated_count
            
        except Exception as e:
            db.rollback()
            raise


# Create singleton instance
progress_service = ProgressService()
