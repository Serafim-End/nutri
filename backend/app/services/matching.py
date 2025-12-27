"""
Matching Service
Simple rule-based matching of clients with nutritionists.
"""

from typing import List
from sqlalchemy import and_, or_

from app.models import NutritionistProfile, Service, Intake


class MatchingService:
    """
    Service for matching clients with nutritionists based on intake answers.
    Uses simple rule-based matching for MVP.
    """

    @staticmethod
    def find_matches(intake: Intake, limit: int = 20) -> List[NutritionistProfile]:
        """
        Find nutritionists matching client's intake criteria.

        Matching rules:
        1. Nutritionist must be approved and active
        2. If goals specified, prefer nutritionists with matching specializations
        3. If budget specified, must have at least one service in range
        4. If dietary restrictions, prefer matching tags

        Args:
            intake: Client intake with answers
            limit: Maximum results to return

        Returns:
            List of matching NutritionistProfile objects, ordered by relevance
        """
        answers = intake.answers or {}

        # Base query: approved and active nutritionists
        query = NutritionistProfile.query.filter(
            NutritionistProfile.verification_status == "approved",
            NutritionistProfile.is_active == True,  # noqa: E712
        )

        # Join with profile for ordering
        query = query.join(NutritionistProfile.profile)

        # Get all matching nutritionists
        nutritionists = query.all()

        # Score and rank
        scored = []
        for n in nutritionists:
            score = MatchingService._calculate_score(n, answers)
            if score > 0:
                scored.append((n, score))

        # Sort by score descending
        scored.sort(key=lambda x: x[1], reverse=True)

        return [n for n, _ in scored[:limit]]

    @staticmethod
    def _calculate_score(nutritionist: NutritionistProfile, answers: dict) -> float:
        """
        Calculate match score for a nutritionist.

        Returns:
            Score from 0.0 to 100.0
        """
        score = 50.0  # Base score for approved nutritionists

        goals = answers.get("goals", [])
        restrictions = answers.get("dietary_restrictions", [])
        budget_min = answers.get("budget_min")
        budget_max = answers.get("budget_max")
        health_conditions = answers.get("health_conditions", [])

        specializations = nutritionist.specializations or []
        tags = nutritionist.tags or []

        # Match goals with specializations (+20 max)
        if goals and specializations:
            goal_matches = len(set(goals) & set(specializations))
            score += min(goal_matches * 5, 20)

        # Match dietary restrictions with tags (+15 max)
        if restrictions and tags:
            restriction_matches = len(set(restrictions) & set(tags))
            score += min(restriction_matches * 5, 15)

        # Match health conditions with specializations (+15 max)
        if health_conditions and specializations:
            condition_matches = len(set(health_conditions) & set(specializations))
            score += min(condition_matches * 5, 15)

        # Check budget range
        if budget_min is not None or budget_max is not None:
            services = Service.query.filter(
                Service.nutritionist_id == nutritionist.nutritionist_id,
                Service.is_active == True,  # noqa: E712
            ).all()

            has_affordable = False
            for service in services:
                price = service.price_rub
                if budget_min and price < budget_min:
                    continue
                if budget_max and price > budget_max:
                    continue
                has_affordable = True
                break

            if not has_affordable and services:
                score -= 30  # Penalize if no affordable services
            elif has_affordable:
                score += 10  # Bonus for having affordable options

        # Bonus for rating
        if nutritionist.rating:
            score += float(nutritionist.rating) * 2  # Up to +10 for 5.0 rating

        # Bonus for reviews
        if nutritionist.reviews_count > 0:
            score += min(nutritionist.reviews_count, 5)  # Up to +5

        return max(score, 0.0)

    @staticmethod
    def search_nutritionists(
        specialization: str = None,
        budget_max: int = None,
        tags: List[str] = None,
        limit: int = 20,
    ) -> List[NutritionistProfile]:
        """
        Search nutritionists by filters (for public browsing).

        Args:
            specialization: Filter by specialization
            budget_max: Maximum price filter
            tags: Filter by tags
            limit: Maximum results

        Returns:
            List of matching nutritionists
        """
        query = NutritionistProfile.query.filter(
            NutritionistProfile.verification_status == "approved",
            NutritionistProfile.is_active == True,  # noqa: E712
        )

        if specialization:
            query = query.filter(
                NutritionistProfile.specializations.any(specialization)
            )

        if tags:
            for tag in tags:
                query = query.filter(NutritionistProfile.tags.any(tag))

        nutritionists = query.all()

        # Filter by budget if specified
        if budget_max is not None:
            result = []
            for n in nutritionists:
                min_price = (
                    Service.query.filter(
                        Service.nutritionist_id == n.nutritionist_id,
                        Service.is_active == True,  # noqa: E712
                    )
                    .with_entities(Service.price_rub)
                    .order_by(Service.price_rub)
                    .first()
                )
                if min_price and min_price[0] <= budget_max:
                    result.append(n)
            nutritionists = result

        # Sort by rating
        nutritionists.sort(
            key=lambda n: (float(n.rating or 0), n.reviews_count), reverse=True
        )

        return nutritionists[:limit]


