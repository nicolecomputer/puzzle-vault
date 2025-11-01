"""Seed database with development data.

This script is for development/testing only.
Run with: pipenv run seed-data
"""

from sqlalchemy.orm import Session

from src.auth import hash_password
from src.config import settings
from src.database import SessionLocal
from src.models.source import Source
from src.models.user import User


def seed_users(db: Session) -> None:
    """Create test users."""
    # Check if users already exist
    existing_user = db.query(User).filter(User.username == "testuser").first()
    if existing_user:
        print("⚠️  Test users already exist, skipping user creation")
        return

    # Create test users with properly hashed passwords
    test_users = [
        User(
            username="admin",
            password_hash=hash_password("password"),
        ),
    ]

    for user in test_users:
        db.add(user)

    db.commit()
    print(f"✓ Created {len(test_users)} test users")
    print("  - admin / password")


def seed_sources(db: Session) -> None:
    """Create test sources."""
    # Get the testuser
    testuser = db.query(User).filter(User.username == "admin").first()
    if not testuser:
        print("⚠️  testuser not found, skipping source creation")
        return

    # Check if sources already exist
    existing_source = db.query(Source).filter(Source.user_id == testuser.id).first()
    if existing_source:
        print("⚠️  Test sources already exist, skipping source creation")
        return

    # Create test sources - folders will be created automatically!
    test_sources = [
        Source(
            name="NYTimes Crossword",
            user_id=testuser.id,
            short_code="nyt",
        ),
        Source(
            name="AVCX",
            user_id=testuser.id,
            short_code="avcx",
        ),
    ]

    for source in test_sources:
        db.add(source)

    db.commit()
    print(f"✓ Created {len(test_sources)} test sources")
    for source in test_sources:
        print(f"  - {source.name} (folder: {source.folder_name})")


def main() -> None:
    """Seed the database with development data."""
    db_path = settings.DATA_PATH / "puzfeed.db"
    print(f"Database: {db_path}\n")

    if not db_path.exists():
        print("❌ Database not found. Run migrations first:")
        print("   pipenv run migrate")
        return

    print("Seeding development data...")

    db = SessionLocal()
    try:
        seed_users(db)
        seed_sources(db)
        print("\n✓ Development data seeded successfully!")
    except Exception as e:
        print(f"\n❌ Error seeding data: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
