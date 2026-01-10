#!/usr/bin/env python3
"""
Seed realistic Russian reviews for all nutritionists.

For each nutritionist, ensures total reviews count is between 5 and 15.
Uses existing client profiles as authors and creates completed bookings.
Updates nutritionist rating and reviews_count to match actual reviews.
"""

import os
import sys
import random
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models import Profile, NutritionistProfile, Review, Booking, Service


POSITIVE_COMMENTS = [
    "Очень внимательный специалист, всё объяснила простым языком.",
    "Получила четкий план и наконец-то понимаю, что и когда есть.",
    "Без воды, всё по делу. Результат заметен уже через пару недель.",
    "Супер подход и поддержка, перестала срываться на сладкое.",
    "Понравилось, что рекомендации реальные и несложные.",
    "Сбалансировали рацион без жестких запретов — это важно для меня.",
    "Подобрали меню под мой график, стало гораздо удобнее.",
    "Очень тактичный и грамотный нутрициолог, рекомендую.",
    "Отличная консультация, чувствую себя намного лучше.",
    "Разобрали анализы и получили понятные шаги, спасибо.",
    "Нормализовался сон и энергия днём, не ожидала так быстро.",
    "Все рекомендации рабочие, с удовольствием продолжаю.",
]

NEUTRAL_COMMENTS = [
    "В целом довольна, есть над чем работать, план понятный.",
    "Хорошая консультация, буду пробовать рекомендации.",
    "Полезно, но потребуется время, чтобы привыкнуть к режиму.",
    "Нормально, некоторые советы уже внедрила.",
    "Понравилась структура, но хочется больше примеров меню.",
]

GOAL_SNIPPETS = [
    "снизить вес",
    "улучшить пищевые привычки",
    "наладить пищеварение",
    "убрать отёки",
    "подготовиться к беременности",
    "восстановиться после стресса",
    "вернуться в форму",
]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def pick_clients() -> list[Profile]:
    clients = Profile.query.filter(Profile.role == "client").all()
    if clients:
        return clients
    return (
        Profile.query.outerjoin(
            NutritionistProfile, Profile.id == NutritionistProfile.nutritionist_id
        )
        .filter(NutritionistProfile.nutritionist_id.is_(None))
        .all()
    )


def pick_comment(rating: int) -> str:
    goal = random.choice(GOAL_SNIPPETS)
    if rating >= 5:
        base = random.choice(POSITIVE_COMMENTS)
    elif rating == 4:
        base = random.choice(POSITIVE_COMMENTS + NEUTRAL_COMMENTS)
    else:
        base = random.choice(NEUTRAL_COMMENTS)
    return f"{base} Цель: {goal}."


def random_rating() -> int:
    return random.choices([5, 4, 3], weights=[60, 30, 10], k=1)[0]


def random_date_within(days: int = 120) -> datetime:
    delta_days = random.randint(3, days)
    delta_hours = random.randint(1, 18)
    return utc_now() - timedelta(days=delta_days, hours=delta_hours)


def recalc_nutritionist_stats(nutritionist_id):
    reviews = Review.query.filter_by(
        nutritionist_id=nutritionist_id,
        is_hidden=False,
    ).all()
    count = len(reviews)
    if count == 0:
        return 0.0, 0
    avg = sum(r.rating for r in reviews) / count
    return round(avg, 2), count


def main():
    app = create_app()
    with app.app_context():
        clients = pick_clients()
        if not clients:
            print("No client profiles found. Create clients first.")
            return

        nutritionists = NutritionistProfile.query.all()
        if not nutritionists:
            print("No nutritionists found.")
            return

        for nutritionist in nutritionists:
            existing_count = Review.query.filter_by(
                nutritionist_id=nutritionist.nutritionist_id
            ).count()
            target = random.randint(5, 15)
            if existing_count >= target:
                print(
                    f"• Nutritionist {nutritionist.nutritionist_id} already has {existing_count} reviews"
                )
                avg, count = recalc_nutritionist_stats(nutritionist.nutritionist_id)
                nutritionist.rating = avg
                nutritionist.reviews_count = count
                continue

            to_create = target - existing_count
            services = Service.query.filter_by(
                nutritionist_id=nutritionist.nutritionist_id
            ).all()

            for _ in range(to_create):
                client = random.choice(clients)
                rating = random_rating()
                comment = pick_comment(rating)
                review_created = random_date_within()
                booking_created = review_created - timedelta(days=random.randint(1, 7))
                paid_at = booking_created + timedelta(hours=random.randint(1, 36))

                service = random.choice(services) if services else None
                price_rub = service.price_rub if service else random.randint(2500, 7000)

                booking = Booking(
                    client_id=client.id,
                    nutritionist_id=nutritionist.nutritionist_id,
                    service_id=service.id if service else None,
                    status="completed",
                    price_rub=price_rub,
                    currency="RUB",
                    created_at=booking_created,
                    paid_at=paid_at,
                )
                db.session.add(booking)
                db.session.flush()

                review = Review(
                    booking_id=booking.id,
                    client_id=client.id,
                    nutritionist_id=nutritionist.nutritionist_id,
                    rating=rating,
                    comment=comment,
                    created_at=review_created,
                    updated_at=review_created,
                )
                db.session.add(review)

            avg, count = recalc_nutritionist_stats(nutritionist.nutritionist_id)
            nutritionist.rating = avg
            nutritionist.reviews_count = count
            print(
                f"✓ Nutritionist {nutritionist.nutritionist_id}: added {to_create} reviews (total {count})"
            )

        db.session.commit()
        print("Done.")


if __name__ == "__main__":
    main()
