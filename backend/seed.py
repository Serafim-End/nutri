#!/usr/bin/env python3
"""
Idempotent seed script for NutriMatch database.

Creates test data that can be run multiple times safely:
- 1 admin user
- 2 nutritionists with profiles, services, and availability slots
- 1 client user

Uses telegram_user_id for idempotency checks to handle existing data.
"""

import os
import sys
from datetime import datetime, timedelta, timezone
from uuid import uuid4

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensions import db
from app.models import (
    Profile,
    NutritionistProfile,
    Service,
    AvailabilitySlot,
)


# ============================================
# FIXED TELEGRAM IDs FOR IDEMPOTENT SEEDING
# ============================================

ADMIN_TELEGRAM_ID = 100000001
NUTRI1_TELEGRAM_ID = 200000001
NUTRI2_TELEGRAM_ID = 200000002
NUTRI3_TELEGRAM_ID = 200000003
NUTRI4_TELEGRAM_ID = 200000004
NUTRI5_TELEGRAM_ID = 200000005
NUTRI6_TELEGRAM_ID = 200000006
NUTRI7_TELEGRAM_ID = 200000007
NUTRI8_TELEGRAM_ID = 200000008
CLIENT_TELEGRAM_ID = 300000001


def utc_now() -> datetime:
    """Get current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


def get_or_create_profile(telegram_user_id: int, full_name: str, role: str, photo_url: str = None) -> tuple[Profile, bool]:
    """
    Get existing profile by telegram_user_id or create new one.
    Returns (profile, created) tuple.
    """
    profile = Profile.query.filter_by(telegram_user_id=telegram_user_id).first()
    
    if profile:
        return profile, False
    
    profile = Profile(
        id=uuid4(),
        telegram_user_id=telegram_user_id,
        full_name=full_name,
        photo_url=photo_url,
        role=role,
    )
    db.session.add(profile)
    return profile, True


def seed_admin() -> Profile:
    """Create or get admin user."""
    profile, created = get_or_create_profile(
        telegram_user_id=ADMIN_TELEGRAM_ID,
        full_name="Admin User",
        role="admin",
    )
    
    if created:
        print(f"✓ Created admin: {profile.full_name}")
    else:
        print(f"• Admin already exists: {profile.full_name}")
    
    return profile


def seed_client() -> Profile:
    """Create or get client user."""
    profile, created = get_or_create_profile(
        telegram_user_id=CLIENT_TELEGRAM_ID,
        full_name="Test Client",
        role="client",
        photo_url="https://api.dicebear.com/7.x/personas/svg?seed=client",
    )
    
    if created:
        print(f"✓ Created client: {profile.full_name}")
    else:
        print(f"• Client already exists: {profile.full_name}")
    
    return profile


def seed_nutritionist_1() -> Profile:
    """Create or get nutritionist 1 (Elena)."""
    profile, created = get_or_create_profile(
        telegram_user_id=NUTRI1_TELEGRAM_ID,
        full_name="Dr. Elena Petrova",
        role="nutritionist",
        photo_url="https://api.dicebear.com/7.x/personas/svg?seed=elena",
    )
    
    if created:
        db.session.flush()
        
        # Create nutritionist profile
        nutri_profile = NutritionistProfile(
            nutritionist_id=profile.id,
            bio="Certified clinical nutritionist with 10 years of experience. "
                "Specializing in weight management, diabetes care, and sports nutrition.",
            tags=["vegetarian", "vegan", "gluten_free", "sports_nutrition"],
            specializations=["weight_loss", "diabetes", "gut_health", "sports_nutrition"],
            verification_status="approved",
            rating=4.85,
            reviews_count=47,
            is_active=True,
            verified_at=utc_now(),
        )
        db.session.add(nutri_profile)
        
        # Create services
        services = [
            Service(
                id=uuid4(),
                nutritionist_id=profile.id,
                title="Initial Consultation",
                description="Comprehensive 60-minute assessment of your health goals, "
                            "dietary habits, and personalized nutrition plan development.",
                duration_minutes=60,
                price_rub=3500,
                is_active=True,
            ),
            Service(
                id=uuid4(),
                nutritionist_id=profile.id,
                title="Follow-up Session",
                description="30-minute progress check and plan adjustments.",
                duration_minutes=30,
                price_rub=2000,
                is_active=True,
            ),
        ]
        for s in services:
            db.session.add(s)
        
        print(f"✓ Created nutritionist: {profile.full_name} with {len(services)} services")
    else:
        # Check if nutritionist profile exists
        if not profile.nutritionist_profile:
            nutri_profile = NutritionistProfile(
                nutritionist_id=profile.id,
                bio="Certified clinical nutritionist with 10 years of experience.",
                tags=["vegetarian", "vegan"],
                specializations=["weight_loss", "diabetes"],
                verification_status="approved",
                rating=4.85,
                reviews_count=47,
                is_active=True,
                verified_at=utc_now(),
            )
            db.session.add(nutri_profile)
            print(f"✓ Added nutritionist profile for: {profile.full_name}")
        else:
            print(f"• Nutritionist already exists: {profile.full_name}")
    
    return profile


def seed_nutritionist_2() -> Profile:
    """Create or get nutritionist 2 (Michael)."""
    profile, created = get_or_create_profile(
        telegram_user_id=NUTRI2_TELEGRAM_ID,
        full_name="Michael Chen, RD",
        role="nutritionist",
        photo_url="https://api.dicebear.com/7.x/personas/svg?seed=michael",
    )
    
    if created:
        db.session.flush()
        
        # Create nutritionist profile
        nutri_profile = NutritionistProfile(
            nutritionist_id=profile.id,
            bio="Registered Dietitian focusing on plant-based nutrition and "
                "holistic wellness. Helping clients achieve balance through mindful eating.",
            tags=["plant_based", "vegan", "holistic", "mindful_eating"],
            specializations=["weight_loss", "plant_based", "mental_wellness", "detox"],
            verification_status="approved",
            rating=4.72,
            reviews_count=31,
            is_active=True,
            verified_at=utc_now(),
        )
        db.session.add(nutri_profile)
        
        # Create services
        services = [
            Service(
                id=uuid4(),
                nutritionist_id=profile.id,
                title="Wellness Consultation",
                description="Holistic 45-minute session focusing on nutrition and lifestyle balance.",
                duration_minutes=45,
                price_rub=2800,
                is_active=True,
            ),
            Service(
                id=uuid4(),
                nutritionist_id=profile.id,
                title="Plant-Based Transition",
                description="Complete guide to transitioning to a plant-based diet. "
                            "Includes meal planning and recipe suggestions.",
                duration_minutes=60,
                price_rub=3200,
                is_active=True,
            ),
        ]
        for s in services:
            db.session.add(s)
        
        print(f"✓ Created nutritionist: {profile.full_name} with {len(services)} services")
    else:
        # Check if nutritionist profile exists
        if not profile.nutritionist_profile:
            nutri_profile = NutritionistProfile(
                nutritionist_id=profile.id,
                bio="Registered Dietitian focusing on plant-based nutrition.",
                tags=["plant_based", "vegan"],
                specializations=["weight_loss", "plant_based"],
                verification_status="approved",
                rating=4.72,
                reviews_count=31,
                is_active=True,
                verified_at=utc_now(),
            )
            db.session.add(nutri_profile)
            print(f"✓ Added nutritionist profile for: {profile.full_name}")
        else:
            print(f"• Nutritionist already exists: {profile.full_name}")
    
    return profile


# Additional nutritionists data for variety
ADDITIONAL_NUTRITIONISTS = [
    {
        "telegram_id": NUTRI3_TELEGRAM_ID,
        "name": "Dr. Anna Sokolova",
        "seed": "anna",
        "bio": "Specialist in sports nutrition with 8 years of experience. Former Olympic team nutritionist. Helping athletes achieve peak performance through optimal nutrition.",
        "tags": ["sports_nutrition", "performance", "supplements", "muscle_gain"],
        "specializations": ["sports_nutrition", "muscle_gain", "weight_loss", "performance"],
        "rating": 4.91,
        "reviews": 63,
        "services": [
            ("Sports Performance Consultation", "Comprehensive nutritional assessment for athletes. Includes body composition analysis and personalized fueling strategies.", 60, 4500),
            ("Athlete Meal Plan", "Custom weekly meal plan designed for your training schedule and competition goals.", 45, 3500),
            ("Pre-Competition Strategy", "Optimize your nutrition for peak performance on competition day.", 30, 2500),
        ],
    },
    {
        "telegram_id": NUTRI4_TELEGRAM_ID,
        "name": "Maria Ivanova, PhD",
        "seed": "maria",
        "bio": "PhD in Nutritional Sciences. Research-backed approach to gut health and digestive wellness. Published author and lecturer.",
        "tags": ["gut_health", "digestive_wellness", "research", "ibs"],
        "specializations": ["gut_health", "better_nutrition", "diabetes", "chronic_conditions"],
        "rating": 4.88,
        "reviews": 42,
        "services": [
            ("Gut Health Assessment", "Comprehensive evaluation of digestive health with personalized recommendations.", 60, 4000),
            ("IBS Management Program", "6-week program to manage IBS symptoms through diet and lifestyle.", 45, 3000),
            ("Follow-up Consultation", "Progress check and plan adjustments.", 30, 1500),
        ],
    },
    {
        "telegram_id": NUTRI5_TELEGRAM_ID,
        "name": "Alexei Volkov",
        "seed": "alexei",
        "bio": "Certified nutritionist specializing in diabetes management and metabolic health. 12 years of clinical experience helping patients manage chronic conditions.",
        "tags": ["diabetes", "metabolic_health", "clinical", "weight_management"],
        "specializations": ["diabetes", "weight_loss", "chronic_conditions", "better_nutrition"],
        "rating": 4.79,
        "reviews": 89,
        "services": [
            ("Diabetes Nutrition Consultation", "Personalized nutrition plan for blood sugar management.", 60, 3500),
            ("Metabolic Health Assessment", "Comprehensive metabolic health evaluation with action plan.", 75, 4500),
            ("Monthly Support Session", "Ongoing support for diabetes management.", 30, 2000),
        ],
    },
    {
        "telegram_id": NUTRI6_TELEGRAM_ID,
        "name": "Olga Kuznetsova",
        "seed": "olga",
        "bio": "Passionate about pregnancy and pediatric nutrition. Helping families raise healthy eaters from conception through childhood.",
        "tags": ["pregnancy", "pediatric", "family", "breastfeeding"],
        "specializations": ["pregnancy", "better_nutrition", "gut_health"],
        "rating": 4.95,
        "reviews": 37,
        "services": [
            ("Pregnancy Nutrition Plan", "Trimester-specific nutrition guidance for a healthy pregnancy.", 60, 3800),
            ("Postpartum & Breastfeeding", "Nutritional support for new mothers and breastfeeding.", 45, 3000),
            ("Pediatric Nutrition Consultation", "Age-appropriate nutrition for infants and children.", 45, 2800),
        ],
    },
    {
        "telegram_id": NUTRI7_TELEGRAM_ID,
        "name": "Dmitry Novikov",
        "seed": "dmitry",
        "bio": "Budget-friendly nutrition expert. Proving that healthy eating doesn't have to be expensive. Meal prep specialist.",
        "tags": ["budget_friendly", "meal_prep", "practical", "weight_management"],
        "specializations": ["weight_loss", "better_nutrition", "meal_planning"],
        "rating": 4.67,
        "reviews": 124,
        "services": [
            ("Budget Nutrition Consultation", "Learn to eat healthy on any budget.", 45, 1500),
            ("Meal Prep Masterclass", "Weekly meal prep strategies that save time and money.", 60, 2000),
            ("Quick Check-in", "15-minute progress check and tips.", 15, 800),
        ],
    },
    {
        "telegram_id": NUTRI8_TELEGRAM_ID,
        "name": "Victoria Smirnova",
        "seed": "victoria",
        "bio": "Holistic nutritionist combining Eastern and Western approaches. Certified in Ayurvedic nutrition and functional medicine.",
        "tags": ["holistic", "ayurveda", "functional", "mental_wellness"],
        "specializations": ["mental_wellness", "gut_health", "detox", "better_nutrition"],
        "rating": 4.82,
        "reviews": 56,
        "services": [
            ("Holistic Health Assessment", "Mind-body-nutrition evaluation with personalized wellness plan.", 90, 5000),
            ("Ayurvedic Consultation", "Discover your dosha and receive personalized dietary recommendations.", 60, 3500),
            ("Stress & Nutrition Session", "How nutrition impacts mental health and stress management.", 45, 2800),
        ],
    },
]


def seed_additional_nutritionist(data: dict) -> Profile:
    """Create or get an additional nutritionist."""
    profile, created = get_or_create_profile(
        telegram_user_id=data["telegram_id"],
        full_name=data["name"],
        role="nutritionist",
        photo_url=f"https://api.dicebear.com/7.x/personas/svg?seed={data['seed']}",
    )
    
    if created:
        db.session.flush()
        
        # Create nutritionist profile
        nutri_profile = NutritionistProfile(
            nutritionist_id=profile.id,
            bio=data["bio"],
            tags=data["tags"],
            specializations=data["specializations"],
            verification_status="approved",
            rating=data["rating"],
            reviews_count=data["reviews"],
            is_active=True,
            verified_at=utc_now(),
        )
        db.session.add(nutri_profile)
        
        # Create services
        for title, description, duration, price in data["services"]:
            service = Service(
                id=uuid4(),
                nutritionist_id=profile.id,
                title=title,
                description=description,
                duration_minutes=duration,
                price_rub=price,
                is_active=True,
            )
            db.session.add(service)
        
        print(f"✓ Created nutritionist: {profile.full_name} with {len(data['services'])} services")
    else:
        if not profile.nutritionist_profile:
            nutri_profile = NutritionistProfile(
                nutritionist_id=profile.id,
                bio=data["bio"],
                tags=data["tags"],
                specializations=data["specializations"],
                verification_status="approved",
                rating=data["rating"],
                reviews_count=data["reviews"],
                is_active=True,
                verified_at=utc_now(),
            )
            db.session.add(nutri_profile)
            print(f"✓ Added nutritionist profile for: {profile.full_name}")
        else:
            print(f"• Nutritionist already exists: {profile.full_name}")
    
    return profile


def seed_availability_slots(profile: Profile, slot_hours: list[int], slots_per_day: int = 5) -> int:
    """
    Create future availability slots for a nutritionist.
    
    Only creates slots if none exist for the nutritionist in the future.
    All times are in UTC.
    """
    if not profile.nutritionist_profile:
        print(f"  ⚠ No nutritionist profile for {profile.full_name}, skipping slots")
        return 0
    
    nutritionist_id = profile.id
    now = utc_now()
    
    # Check if future slots already exist
    existing_future_slots = AvailabilitySlot.query.filter(
        AvailabilitySlot.nutritionist_id == nutritionist_id,
        AvailabilitySlot.start_at > now,
    ).count()
    
    if existing_future_slots > 0:
        print(f"  • {existing_future_slots} future slots already exist for {profile.full_name}")
        return 0
    
    # Create slots for next 7 days
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    created_count = 0
    
    for day_offset in range(1, 8):  # Days 1-7 from today
        day = today + timedelta(days=day_offset)
        
        # Create slots for specified hours (up to slots_per_day)
        for hour in slot_hours[:slots_per_day]:
            slot_start = day.replace(hour=hour)
            slot_end = slot_start + timedelta(hours=1)
            
            slot = AvailabilitySlot(
                nutritionist_id=nutritionist_id,
                start_at=slot_start,
                end_at=slot_end,
                status="free",
            )
            db.session.add(slot)
            created_count += 1
    
    return created_count


def seed_database():
    """Main seed function - idempotent."""
    app = create_app()
    
    with app.app_context():
        print("\n" + "=" * 50)
        print("NutriMatch Database Seed")
        print("=" * 50 + "\n")
        
        # Seed users
        print("Creating users...")
        seed_admin()
        seed_client()
        nutri1 = seed_nutritionist_1()
        nutri2 = seed_nutritionist_2()
        
        # Seed additional nutritionists
        additional_nutris = []
        for nutri_data in ADDITIONAL_NUTRITIONISTS:
            nutri = seed_additional_nutritionist(nutri_data)
            additional_nutris.append(nutri)
        
        # Commit users and profiles
        db.session.commit()
        
        # Seed availability slots
        print("\nCreating availability slots...")
        
        # Nutritionist 1: morning and afternoon slots
        slots1 = seed_availability_slots(
            nutri1, 
            slot_hours=[9, 10, 11, 14, 15, 16],
            slots_per_day=5,
        )
        if slots1 > 0:
            print(f"  ✓ Created {slots1} slots for {nutri1.full_name}")
        
        # Nutritionist 2: different schedule
        slots2 = seed_availability_slots(
            nutri2, 
            slot_hours=[10, 12, 14, 16, 18],
            slots_per_day=5,
        )
        if slots2 > 0:
            print(f"  ✓ Created {slots2} slots for {nutri2.full_name}")
        
        # Additional nutritionists: varied schedules
        slot_schedules = [
            [8, 9, 10, 11, 12],      # Early morning
            [11, 13, 15, 17, 19],    # Midday to evening
            [9, 11, 14, 16, 18],     # Mixed
            [10, 12, 14, 16, 18],    # Afternoon focus
            [8, 10, 12, 14, 16],     # Morning to afternoon
            [12, 14, 16, 18, 20],    # Afternoon to evening
        ]
        
        for i, nutri in enumerate(additional_nutris):
            schedule = slot_schedules[i % len(slot_schedules)]
            slots = seed_availability_slots(nutri, slot_hours=schedule, slots_per_day=5)
            if slots > 0:
                print(f"  ✓ Created {slots} slots for {nutri.full_name}")
        
        # Final commit
        db.session.commit()
        
        # Print summary
        print("\n" + "=" * 50)
        print("✅ Seed completed successfully!")
        print("=" * 50)
        print("\nTest Accounts:")
        print(f"  Admin:        telegram_user_id = {ADMIN_TELEGRAM_ID}")
        print(f"  Client:       telegram_user_id = {CLIENT_TELEGRAM_ID}")
        print(f"  Nutritionist: telegram_user_id = {NUTRI1_TELEGRAM_ID} (Elena)")
        print(f"  Nutritionist: telegram_user_id = {NUTRI2_TELEGRAM_ID} (Michael)")
        print(f"  + {len(ADDITIONAL_NUTRITIONISTS)} more nutritionists")
        print("\nFor debug mode auth, use init_data like: test_200000001_Elena")
        print()


if __name__ == "__main__":
    seed_database()
