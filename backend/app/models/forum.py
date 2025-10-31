"""
Forum database models
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class ForumCategory(Base):
    """
    Forum category model
    Represents a high-level grouping of topics (e.g., "General Discussion", "Design Help")
    """

    __tablename__ = "forum_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    slug = Column(String(100), nullable=False, unique=True, index=True)
    order = Column(Integer, default=0)  # For custom ordering
    icon = Column(String(50), nullable=True)  # Icon name from lucide-react

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    topics = relationship("ForumTopic", back_populates="category", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ForumCategory(id={self.id}, name={self.name})>"


class ForumTopic(Base):
    """
    Forum topic (thread) model
    Represents a discussion thread within a category
    """

    __tablename__ = "forum_topics"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    slug = Column(String(200), nullable=False, index=True)

    # Category relationship
    category_id = Column(Integer, ForeignKey("forum_categories.id"), nullable=False)
    category = relationship("ForumCategory", back_populates="topics")

    # Author relationship
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    author = relationship("User")

    # Topic metadata
    is_pinned = Column(Boolean, default=False)
    is_locked = Column(Boolean, default=False)
    views_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_post_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    posts = relationship("ForumPost", back_populates="topic", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ForumTopic(id={self.id}, title={self.title})>"


class ForumPost(Base):
    """
    Forum post model
    Represents an individual message within a topic
    """

    __tablename__ = "forum_posts"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)

    # Topic relationship
    topic_id = Column(Integer, ForeignKey("forum_topics.id"), nullable=False)
    topic = relationship("ForumTopic", back_populates="posts")

    # Author relationship
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    author = relationship("User")

    # Post metadata
    is_edited = Column(Boolean, default=False)
    edited_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<ForumPost(id={self.id}, topic_id={self.topic_id})>"
