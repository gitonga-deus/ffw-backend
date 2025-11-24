from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime


class CourseResponse(BaseModel):
    """Schema for course response."""
    id: str
    title: str
    description: str
    price: float
    currency: str
    instructor_name: str
    instructor_bio: Optional[str] = None
    instructor_image_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    is_published: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class ModuleResponse(BaseModel):
    """Schema for module response."""
    id: str
    course_id: str
    title: str
    description: Optional[str] = None
    order_index: int
    is_published: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class ContentResponse(BaseModel):
    """Schema for content response."""
    id: str
    module_id: str
    content_type: str
    title: str
    order_index: int
    
    # Video specific fields
    vimeo_video_id: Optional[str] = None
    video_duration: Optional[int] = None
    
    # PDF specific fields
    pdf_url: Optional[str] = None
    pdf_filename: Optional[str] = None
    
    # Rich text specific fields
    rich_text_content: Optional[Any] = None  # JSON data
    
    # Exercise specific fields
    exercise: Optional[dict] = None
    
    is_published: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class ModuleWithContentResponse(BaseModel):
    """Schema for module with its content items."""
    id: str
    course_id: str
    title: str
    description: Optional[str] = None
    order_index: int
    is_published: bool
    content_items: List[ContentResponse] = []
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class ContentCreate(BaseModel):
    """Schema for creating content."""
    module_id: str
    content_type: str = Field(..., pattern="^(video|pdf|rich_text|exercise)$")
    title: str = Field(..., min_length=1, max_length=255)
    order_index: int = Field(..., ge=0)
    
    # Video specific fields
    vimeo_video_id: Optional[str] = None
    video_duration: Optional[int] = None
    
    # PDF specific fields
    pdf_filename: Optional[str] = None
    
    # Rich text specific fields
    rich_text_content: Optional[Any] = None
    
    # Exercise specific fields
    exercise_data: Optional[dict] = None
    
    is_published: bool = False


class ContentUpdate(BaseModel):
    """Schema for updating content."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    order_index: Optional[int] = Field(None, ge=0)
    
    # Video specific fields
    vimeo_video_id: Optional[str] = None
    video_duration: Optional[int] = None
    
    # PDF specific fields
    pdf_filename: Optional[str] = None
    
    # Rich text specific fields
    rich_text_content: Optional[Any] = None
    
    is_published: Optional[bool] = None


class ModuleCreate(BaseModel):
    """Schema for creating a module."""
    course_id: str
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    order_index: int = Field(..., ge=0)
    is_published: bool = False


class ModuleUpdate(BaseModel):
    """Schema for updating a module."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    order_index: Optional[int] = Field(None, ge=0)
    is_published: Optional[bool] = None


class ContentOrderItem(BaseModel):
    """Schema for a single content order item."""
    id: str
    order_index: int = Field(..., ge=0)


class ContentReorderRequest(BaseModel):
    """Schema for reordering content items."""
    items: List[ContentOrderItem]
