"""
Forum API endpoints
Handles categories, topics, and posts
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import re

from app.core.security import get_current_user, get_optional_user
from app.db.session import get_db
from app.models.user import User
from app.models.forum import ForumCategory, ForumTopic, ForumPost
from app.schemas.forum import (
    ForumCategoryResponse,
    ForumTopicCreate,
    ForumTopicUpdate,
    ForumTopicListItem,
    ForumTopicResponse,
    ForumPostCreate,
    ForumPostUpdate,
    ForumPostResponse,
)

router = APIRouter()


def generate_slug(text: str) -> str:
    """Generate URL-friendly slug from text"""
    slug = re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')
    return slug[:100]  # Limit length


# ==================== Categories ====================

@router.get("/categories", response_model=List[ForumCategoryResponse])
async def list_categories(
    db: Session = Depends(get_db)
):
    """
    List all forum categories

    - Public endpoint, no authentication required
    - Returns categories with topic/post counts
    """
    categories = db.query(ForumCategory).order_by(ForumCategory.order, ForumCategory.name).all()

    # Add computed fields
    result = []
    for category in categories:
        topic_count = db.query(func.count(ForumTopic.id)).filter(
            ForumTopic.category_id == category.id
        ).scalar()

        post_count = db.query(func.count(ForumPost.id)).join(ForumTopic).filter(
            ForumTopic.category_id == category.id
        ).scalar()

        category_dict = {
            "id": category.id,
            "name": category.name,
            "description": category.description,
            "slug": category.slug,
            "order": category.order,
            "icon": category.icon,
            "created_at": category.created_at,
            "updated_at": category.updated_at,
            "topic_count": topic_count or 0,
            "post_count": post_count or 0,
        }
        result.append(ForumCategoryResponse(**category_dict))

    return result


# ==================== Topics ====================

@router.post("/topics", response_model=ForumTopicResponse, status_code=status.HTTP_201_CREATED)
async def create_topic(
    topic_data: ForumTopicCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new forum topic

    - Requires authentication
    - Creates topic and first post
    """
    # Verify category exists
    category = db.query(ForumCategory).filter(ForumCategory.id == topic_data.category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )

    # Generate slug
    slug = generate_slug(topic_data.title)

    # Check for duplicate slug in this category
    counter = 1
    original_slug = slug
    while db.query(ForumTopic).filter(
        ForumTopic.slug == slug,
        ForumTopic.category_id == topic_data.category_id
    ).first():
        slug = f"{original_slug}-{counter}"
        counter += 1

    # Create topic
    new_topic = ForumTopic(
        title=topic_data.title,
        slug=slug,
        category_id=topic_data.category_id,
        author_id=current_user.id
    )
    db.add(new_topic)
    db.flush()  # Get topic ID

    # Create first post
    first_post = ForumPost(
        content=topic_data.content,
        topic_id=new_topic.id,
        author_id=current_user.id
    )
    db.add(first_post)
    db.commit()
    db.refresh(new_topic)

    # Build response with computed fields
    return ForumTopicResponse(
        id=new_topic.id,
        title=new_topic.title,
        slug=new_topic.slug,
        category_id=new_topic.category_id,
        category_name=category.name,
        author_id=new_topic.author_id,
        author_username=current_user.username,
        is_pinned=new_topic.is_pinned,
        is_locked=new_topic.is_locked,
        views_count=new_topic.views_count,
        created_at=new_topic.created_at,
        updated_at=new_topic.updated_at,
        last_post_at=new_topic.last_post_at
    )


@router.get("/categories/{category_id}/topics", response_model=List[ForumTopicListItem])
async def list_topics_in_category(
    category_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List topics in a category

    - Public endpoint
    - Pinned topics appear first
    - Sorted by last_post_at
    """
    # Verify category exists
    category = db.query(ForumCategory).filter(ForumCategory.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )

    topics = (
        db.query(ForumTopic)
        .filter(ForumTopic.category_id == category_id)
        .order_by(ForumTopic.is_pinned.desc(), ForumTopic.last_post_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    # Build response with computed fields
    result = []
    for topic in topics:
        post_count = db.query(func.count(ForumPost.id)).filter(
            ForumPost.topic_id == topic.id
        ).scalar()

        result.append(ForumTopicListItem(
            id=topic.id,
            title=topic.title,
            slug=topic.slug,
            category_id=topic.category_id,
            author_id=topic.author_id,
            author_username=topic.author.username,
            is_pinned=topic.is_pinned,
            is_locked=topic.is_locked,
            views_count=topic.views_count,
            post_count=post_count or 0,
            created_at=topic.created_at,
            last_post_at=topic.last_post_at
        ))

    return result


@router.get("/topics/{topic_id}", response_model=ForumTopicResponse)
async def get_topic(
    topic_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get topic details

    - Public endpoint
    - Increments view count
    """
    topic = db.query(ForumTopic).filter(ForumTopic.id == topic_id).first()

    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic not found"
        )

    # Increment view count
    topic.views_count += 1
    db.commit()

    return ForumTopicResponse(
        id=topic.id,
        title=topic.title,
        slug=topic.slug,
        category_id=topic.category_id,
        category_name=topic.category.name,
        author_id=topic.author_id,
        author_username=topic.author.username,
        is_pinned=topic.is_pinned,
        is_locked=topic.is_locked,
        views_count=topic.views_count,
        created_at=topic.created_at,
        updated_at=topic.updated_at,
        last_post_at=topic.last_post_at
    )


@router.put("/topics/{topic_id}", response_model=ForumTopicResponse)
async def update_topic(
    topic_id: int,
    topic_data: ForumTopicUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update topic

    - Only topic author can update title
    - Admins can update is_pinned and is_locked
    """
    topic = db.query(ForumTopic).filter(ForumTopic.id == topic_id).first()

    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic not found"
        )

    # Check permissions
    if topic.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only topic author can update"
        )

    # Update fields
    if topic_data.title is not None:
        topic.title = topic_data.title
        topic.slug = generate_slug(topic_data.title)

    if topic_data.is_pinned is not None:
        topic.is_pinned = topic_data.is_pinned

    if topic_data.is_locked is not None:
        topic.is_locked = topic_data.is_locked

    db.commit()
    db.refresh(topic)

    return ForumTopicResponse(
        id=topic.id,
        title=topic.title,
        slug=topic.slug,
        category_id=topic.category_id,
        category_name=topic.category.name,
        author_id=topic.author_id,
        author_username=topic.author.username,
        is_pinned=topic.is_pinned,
        is_locked=topic.is_locked,
        views_count=topic.views_count,
        created_at=topic.created_at,
        updated_at=topic.updated_at,
        last_post_at=topic.last_post_at
    )


@router.delete("/topics/{topic_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_topic(
    topic_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete topic

    - Only topic author can delete
    """
    topic = db.query(ForumTopic).filter(ForumTopic.id == topic_id).first()

    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic not found"
        )

    if topic.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only topic author can delete"
        )

    db.delete(topic)
    db.commit()

    return None


# ==================== Posts ====================

@router.get("/topics/{topic_id}/posts", response_model=List[ForumPostResponse])
async def list_posts_in_topic(
    topic_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List posts in a topic

    - Public endpoint
    - Sorted by created_at
    """
    # Verify topic exists
    topic = db.query(ForumTopic).filter(ForumTopic.id == topic_id).first()
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic not found"
        )

    posts = (
        db.query(ForumPost)
        .filter(ForumPost.topic_id == topic_id)
        .order_by(ForumPost.created_at.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    # Build response with computed fields
    return [
        ForumPostResponse(
            id=post.id,
            content=post.content,
            topic_id=post.topic_id,
            author_id=post.author_id,
            author_username=post.author.username,
            is_edited=post.is_edited,
            edited_at=post.edited_at,
            created_at=post.created_at,
            updated_at=post.updated_at
        )
        for post in posts
    ]


@router.post("/topics/{topic_id}/posts", response_model=ForumPostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    topic_id: int,
    post_data: ForumPostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new post in a topic

    - Requires authentication
    - Cannot post to locked topics
    """
    # Verify topic exists
    topic = db.query(ForumTopic).filter(ForumTopic.id == topic_id).first()
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic not found"
        )

    # Check if topic is locked
    if topic.is_locked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot post to locked topic"
        )

    # Create post
    new_post = ForumPost(
        content=post_data.content,
        topic_id=topic_id,
        author_id=current_user.id
    )
    db.add(new_post)

    # Update topic's last_post_at
    topic.last_post_at = func.now()

    db.commit()
    db.refresh(new_post)

    return ForumPostResponse(
        id=new_post.id,
        content=new_post.content,
        topic_id=new_post.topic_id,
        author_id=new_post.author_id,
        author_username=current_user.username,
        is_edited=new_post.is_edited,
        edited_at=new_post.edited_at,
        created_at=new_post.created_at,
        updated_at=new_post.updated_at
    )


@router.put("/posts/{post_id}", response_model=ForumPostResponse)
async def update_post(
    post_id: int,
    post_data: ForumPostUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a post

    - Only post author can update
    """
    post = db.query(ForumPost).filter(ForumPost.id == post_id).first()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )

    if post.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only post author can update"
        )

    # Update post
    post.content = post_data.content
    post.is_edited = True
    post.edited_at = func.now()

    db.commit()
    db.refresh(post)

    return ForumPostResponse(
        id=post.id,
        content=post.content,
        topic_id=post.topic_id,
        author_id=post.author_id,
        author_username=post.author.username,
        is_edited=post.is_edited,
        edited_at=post.edited_at,
        created_at=post.created_at,
        updated_at=post.updated_at
    )


@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a post

    - Only post author can delete
    - Cannot delete first post (must delete topic instead)
    """
    post = db.query(ForumPost).filter(ForumPost.id == post_id).first()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )

    if post.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only post author can delete"
        )

    # Check if this is the first post
    first_post = (
        db.query(ForumPost)
        .filter(ForumPost.topic_id == post.topic_id)
        .order_by(ForumPost.created_at.asc())
        .first()
    )

    if first_post.id == post.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete first post. Delete the topic instead."
        )

    db.delete(post)
    db.commit()

    return None
