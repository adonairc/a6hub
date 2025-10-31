#!/usr/bin/env python3
"""
Seed forum categories

Creates initial forum categories for the a6hub community forum.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.db.session import engine
from app.models.forum import ForumCategory

def seed_categories():
    """Create initial forum categories"""

    categories = [
        {
            "name": "General Discussion",
            "description": "Talk about anything related to chip design, hardware, and electronics",
            "slug": "general-discussion",
            "order": 1,
            "icon": "MessageSquare"
        },
        {
            "name": "Design Help",
            "description": "Get help with your chip designs, HDL code, and design challenges",
            "slug": "design-help",
            "order": 2,
            "icon": "HelpCircle"
        },
        {
            "name": "Show & Tell",
            "description": "Share your completed projects, designs, and achievements",
            "slug": "show-and-tell",
            "order": 3,
            "icon": "Star"
        },
        {
            "name": "Simulation & Verification",
            "description": "Discuss simulation tools, testbenches, and verification methodologies",
            "slug": "simulation-verification",
            "order": 4,
            "icon": "Zap"
        },
        {
            "name": "Synthesis & Physical Design",
            "description": "Topics about RTL-to-GDSII flow, place & route, and timing closure",
            "slug": "synthesis-physical-design",
            "order": 5,
            "icon": "Cpu"
        },
        {
            "name": "Tools & Resources",
            "description": "Share and discuss EDA tools, PDKs, IP cores, and learning resources",
            "slug": "tools-resources",
            "order": 6,
            "icon": "Wrench"
        },
        {
            "name": "Feedback & Suggestions",
            "description": "Provide feedback about a6hub and suggest new features",
            "slug": "feedback-suggestions",
            "order": 7,
            "icon": "Lightbulb"
        },
    ]

    print("=" * 60)
    print("Seeding Forum Categories")
    print("=" * 60)
    print()

    db = Session(bind=engine)

    try:
        for cat_data in categories:
            # Check if category already exists
            existing = db.query(ForumCategory).filter(
                ForumCategory.slug == cat_data["slug"]
            ).first()

            if existing:
                print(f"✓ Category '{cat_data['name']}' already exists (ID: {existing.id})")
                continue

            # Create category
            category = ForumCategory(**cat_data)
            db.add(category)
            db.flush()

            print(f"✓ Created category '{cat_data['name']}' (ID: {category.id})")

        db.commit()

        print()
        print("=" * 60)
        print("Seeding completed successfully!")
        print("=" * 60)

        # Show summary
        total_categories = db.query(ForumCategory).count()
        print(f"\nTotal categories in database: {total_categories}")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    seed_categories()
