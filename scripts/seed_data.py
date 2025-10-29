"""Seed database with development data.

This script is for development/testing only.
Run with: pipenv run seed-data
"""
from sqlalchemy.orm import Session
from src.database import SessionLocal, DATABASE_PATH
from src.models.user import User
from src.auth import hash_password


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
            username="testuser",
            password_hash=hash_password("password"),

        ),
        User(
            username="admin",
            password_hash=hash_password("password"),
        ),
    ]

    for user in test_users:
        db.add(user)

    db.commit()
    print(f"✓ Created {len(test_users)} test users")
    print("  - testuser / password")
    print("  - admin / password")


def main() -> None:
    """Seed the database with development data."""
    print(f"Database: {DATABASE_PATH}\n")

    if not DATABASE_PATH.exists():
        print("❌ Database not found. Run migrations first:")
        print("   pipenv run migrate")
        return

    print("Seeding development data...")

    db = SessionLocal()
    try:
        seed_users(db)
        print("\n✓ Development data seeded successfully!")
    except Exception as e:
        print(f"\n❌ Error seeding data: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
