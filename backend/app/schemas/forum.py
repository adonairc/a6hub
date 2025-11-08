"""
Pydantic schemas for Forum models
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# Category Schemas
class ForumCategoryCreate(BaseModel):
    """Schema for creating a forum category"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    slug: str = Field(..., min_length=1, max_length=100)
    order: int = 0
    icon: Optional[str] = None


class ForumCategoryUpdate(BaseModel):
    """Schema for updating a forum category"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    order: Optional[int] = None
    icon: Optional[str] = None


class ForumCategoryResponse(BaseModel):
    """Schema for forum category in responses"""
    id: int
    name: str
    description: Optional[str]
    slug: str
    order: int
    icon: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    topic_count: int = 0  # Computed field
    post_count: int = 0  # Computed field

    model_config = {"from_attributes": True}


# Topic Schemas
class ForumTopicCreate(BaseModel):
    """Schema for creating a forum topic"""
    title: str = Field(..., min_length=1, max_length=200)
    category_id: int
    content: str = Field(..., min_length=1)  # First post content


class ForumTopicUpdate(BaseModel):
    """Schema for updating a forum topic"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    is_pinned: Optional[bool] = None
    is_locked: Optional[bool] = None


class ForumTopicListItem(BaseModel):
    """Schema for topic in list views"""
    id: int
    title: str
    slug: str
    category_id: int
    author_id: int
    author_username: str  # Computed field
    is_pinned: bool
    is_locked: bool
    views_count: int
    post_count: int  # Computed field
    created_at: datetime
    last_post_at: datetime

    model_config = {"from_attributes": True}


class ForumTopicResponse(BaseModel):
    """Schema for full topic details"""
    id: int
    title: str
    slug: str
    category_id: int
    category_name: str  # Computed field
    author_id: int
    author_username: str  # Computed field
    is_pinned: bool
    is_locked: bool
    views_count: int
    created_at: datetime
    updated_at: Optional[datetime]
    last_post_at: datetime

    model_config = {"from_attributes": True}


# Post Schemas
class ForumPostCreate(BaseModel):
    """Schema for creating a forum post"""
    content: str = Field(..., min_length=1)


class ForumPostUpdate(BaseModel):
    """Schema for updating a forum post"""
    content: str = Field(..., min_length=1)


class ForumPostResponse(BaseModel):
    """Schema for forum post in responses"""
    id: int
    content: str
    topic_id: int
    author_id: int
    author_username: str  # Computed field
    is_edited: bool
    edited_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}
