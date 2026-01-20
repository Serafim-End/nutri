#!/usr/bin/env python3
"""
Test User Seeder Script
Creates test users (client and nutritionist) for development and QA testing.

Usage:
    python scripts/seed_test_users.py

Environment variables required:
    - DATABASE_URL: PostgreSQL connection string
    
Optional:
    - TEST_CLIENT_TELEGRAM_ID: Telegram user ID for test client (default: 111111111)
    - TEST_NUTRITIONIST_TELEGRAM_ID: Telegram user ID for test nutritionist (default: 222222222)
"""

import asyncio
import os
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncpg


# Default test user IDs
DEFAULT_CLIENT_TELEGRAM_ID = 111111111
DEFAULT_NUTRITIONIST_TELEGRAM_ID = 222222222


async def get_db_connection() -> asyncpg.Connection:
    """Get database connection."""
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is required")
    
    # Convert URL format if needed
    if "+psycopg2" in database_url:
        database_url = database_url.replace("+psycopg2", "")
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    return await asyncpg.connect(database_url)


async def seed_test_client(conn: asyncpg.Connection, telegram_id: int) -> dict:
    """Create or update test client user."""
    # Check if profile exists
    existing = await conn.fetchrow(
        "SELECT id, full_name, role FROM profiles WHERE telegram_user_id = $1",
        telegram_id
    )
    
    if existing:
        print(f"  ✓ Test client already exists: id={existing['id']}, name={existing['full_name']}")
        return {
            "id": str(existing["id"]),
            "telegram_user_id": telegram_id,
            "full_name": existing["full_name"],
            "role": existing["role"],
            "is_new": False,
        }
    
    # Create new profile
    import uuid
    profile_id = str(uuid.uuid4())
    
    await conn.execute("""
        INSERT INTO profiles (id, telegram_user_id, full_name, role, created_at, updated_at)
        VALUES ($1, $2, $3, $4, $5, $5)
    """, profile_id, telegram_id, "Test Client", "client", datetime.utcnow())
    
    print(f"  ✓ Created test client: id={profile_id}, telegram_id={telegram_id}")
    
    return {
        "id": profile_id,
        "telegram_user_id": telegram_id,
        "full_name": "Test Client",
        "role": "client",
        "is_new": True,
    }


async def seed_test_nutritionist(conn: asyncpg.Connection, telegram_id: int) -> dict:
    """Create or update test nutritionist user."""
    import uuid
    
    # Check if profile exists
    existing = await conn.fetchrow(
        "SELECT id, full_name, role FROM profiles WHERE telegram_user_id = $1",
        telegram_id
    )
    
    if existing:
        # Check for nutritionist profile
        nutritionist = await conn.fetchrow(
            "SELECT nutritionist_id, verification_status FROM nutritionist_profiles WHERE nutritionist_id = $1",
            existing["id"]
        )
        
        if nutritionist:
            print(f"  ✓ Test nutritionist already exists: id={existing['id']}, status={nutritionist['verification_status']}")
            return {
                "id": str(existing["id"]),
                "telegram_user_id": telegram_id,
                "full_name": existing["full_name"],
                "role": existing["role"],
                "verification_status": nutritionist["verification_status"],
                "is_new": False,
            }
    
    # Create new profile
    profile_id = existing["id"] if existing else str(uuid.uuid4())
    
    if not existing:
        await conn.execute("""
            INSERT INTO profiles (id, telegram_user_id, full_name, role, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $5)
        """, profile_id, telegram_id, "Test Nutritionist", "nutritionist", datetime.utcnow())
        print(f"  ✓ Created profile: id={profile_id}")
    else:
        await conn.execute("""
            UPDATE profiles SET role = 'nutritionist', updated_at = $2 WHERE id = $1
        """, profile_id, datetime.utcnow())
    
    # Create nutritionist profile
    await conn.execute("""
        INSERT INTO nutritionist_profiles (nutritionist_id, bio, verification_status, specializations, tags, created_at, updated_at)
        VALUES ($1, $2, $3, $4, $5, $6, $6)
        ON CONFLICT (nutritionist_id) DO UPDATE SET
            verification_status = 'approved',
            updated_at = $6
    """, 
        profile_id,
        "Опытный нутрициолог с 10-летним стажем. Специализируюсь на спортивном питании и снижении веса.",
        "approved",  # Pre-approve for testing
        ["weight_loss", "sports_nutrition"],
        ["online_only"],
        datetime.utcnow()
    )
    
    print(f"  ✓ Created/updated nutritionist profile: id={profile_id}")
    
    # Create a test service
    service_id = str(uuid.uuid4())
    await conn.execute("""
        INSERT INTO services (id, nutritionist_id, title, description, duration_minutes, price_rub, is_active, created_at, updated_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $8)
        ON CONFLICT DO NOTHING
    """,
        service_id,
        profile_id,
        "Консультация по питанию",
        "Индивидуальная консультация по составлению рациона",
        60,
        3000,
        True,
        datetime.utcnow()
    )
    
    print(f"  ✓ Created test service: id={service_id}")
    
    return {
        "id": profile_id,
        "telegram_user_id": telegram_id,
        "full_name": "Test Nutritionist",
        "role": "nutritionist",
        "verification_status": "approved",
        "is_new": True,
    }


async def main():
    """Main entry point."""
    print("🌱 NutriMatch Test User Seeder")
    print("=" * 40)
    
    # Get telegram IDs from environment or use defaults
    client_id = int(os.environ.get("TEST_CLIENT_TELEGRAM_ID", DEFAULT_CLIENT_TELEGRAM_ID))
    nutritionist_id = int(os.environ.get("TEST_NUTRITIONIST_TELEGRAM_ID", DEFAULT_NUTRITIONIST_TELEGRAM_ID))
    
    print(f"\nTest Client Telegram ID: {client_id}")
    print(f"Test Nutritionist Telegram ID: {nutritionist_id}")
    print()
    
    try:
        conn = await get_db_connection()
        print("✅ Connected to database\n")
        
        # Seed client
        print("📱 Seeding test client...")
        client = await seed_test_client(conn, client_id)
        
        print("\n👩‍⚕️ Seeding test nutritionist...")
        nutritionist = await seed_test_nutritionist(conn, nutritionist_id)
        
        await conn.close()
        
        print("\n" + "=" * 40)
        print("✅ Seeding complete!\n")
        
        print("📋 Test Users Summary:")
        print(f"  Client:       telegram_id={client_id}, profile_id={client['id']}")
        print(f"  Nutritionist: telegram_id={nutritionist_id}, profile_id={nutritionist['id']}")
        
        print("\n💡 To use these users:")
        print(f"  1. In Telegram, find your bot")
        print(f"  2. Use account with telegram_id={client_id} for client testing")
        print(f"  3. Use account with telegram_id={nutritionist_id} for nutritionist testing")
        print(f"  4. Or update TEST_*_TELEGRAM_ID env vars to your actual IDs")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
