"""
Matching Service
Simple rule-based matching of clients with nutritionists.
"""

from typing import List, Dict, Any, Tuple
from sqlalchemy import and_, or_

from app.models import NutritionistProfile, Service, Intake
from app.services.filters import FILTER_OPTIONS


# Help mode to service title keyword mapping
HELP_MODE_KEYWORDS = {
    "one_time": ["консультация", "consultation", "разовая", "single", "первичная"],
    "plan": ["план", "plan", "программа", "program", "рацион", "меню"],
    "long_term": ["сопровождение", "support", "курс", "course", "месяц", "month"],
}

LABELS_BY_ID = {
    item["id"]: item["label"]
    for group in FILTER_OPTIONS.values()
    for item in group
}

EXTRA_LABELS = {
    "plant_based": "Растительное питание",
    "holistic": "Холистический подход",
    "mindful_eating": "Осознанное питание",
    "performance": "Результативность",
    "digestive_wellness": "Здоровое пищеварение",
    "research": "Научный подход",
    "ibs": "СРК",
    "metabolic_health": "Метаболическое здоровье",
    "clinical": "Клиническое питание",
    "family": "Семейное питание",
    "breastfeeding": "Грудное вскармливание",
    "pediatric": "Педиатрия",
    "budget_friendly": "Бюджетное питание",
    "meal_prep": "Заготовки еды",
    "practical": "Практичный подход",
    "ayurveda": "Аюрведа",
    "functional": "Функциональная медицина",
}


def _label_for(value: str) -> str:
    return LABELS_BY_ID.get(value) or EXTRA_LABELS.get(value) or value.replace("_", " ")


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
            NutritionistProfile.is_blocked == False,  # noqa: E712
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
            NutritionistProfile.is_blocked == False,  # noqa: E712
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

    @staticmethod
    def search_with_filters(
        filters: Dict[str, Any],
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Search nutritionists by filters with scoring and matched reasons.
        
        Args:
            filters: Filter dict with keys:
                - goals: List of goal IDs
                - topics: List of topic IDs
                - budget_max_rub: Max budget or None
                - dietary: List of dietary restriction IDs
                - help_mode: "one_time" | "plan" | "long_term" | None
                - specializations: List of specialization strings
                - tags: List of tag strings
            limit: Maximum results to return
            
        Returns:
            List of dicts with nutritionist data, score, and matched_reasons
        """
        # Base query: approved and active nutritionists
        query = NutritionistProfile.query.filter(
            NutritionistProfile.verification_status == "approved",
            NutritionistProfile.is_active == True,  # noqa: E712
            NutritionistProfile.is_blocked == False,  # noqa: E712
        )
        
        # Join with profile for data
        query = query.join(NutritionistProfile.profile)
        
        nutritionists = query.all()
        
        # Extract filter values
        goals = filters.get("goals", []) or []
        topics = filters.get("topics", []) or []
        budget_max = filters.get("budget_max_rub")
        dietary = filters.get("dietary", []) or []
        help_mode = filters.get("help_mode")
        filter_specs = filters.get("specializations", []) or []
        filter_tags = filters.get("tags", []) or []
        
        # Combine goals with specializations for matching
        all_specs = set(goals) | set(filter_specs)
        # Combine dietary with tags for matching
        all_tags = set(dietary) | set(topics) | set(filter_tags)
        
        results = []
        
        for n in nutritionists:
            score = 0
            matched_reasons = []
            
            n_specs = set(n.specializations or [])
            n_tags = set(n.tags or [])
            
            # Score: +3 per overlap between goals and nutritionist specializations
            goal_overlaps = all_specs & n_specs
            if goal_overlaps:
                score += len(goal_overlaps) * 3
                for g in list(goal_overlaps)[:2]:  # Show max 2 reasons
                    matched_reasons.append(f"Специализация: {_label_for(g)}")
            
            # Score: +1 per overlap between topics/dietary and nutritionist tags
            tag_overlaps = all_tags & (n_tags | n_specs)
            if tag_overlaps:
                score += len(tag_overlaps) * 1
                for t in list(tag_overlaps)[:2]:
                    if t not in goal_overlaps:  # Don't duplicate
                        matched_reasons.append(f"Опыт работы с: {_label_for(t)}")
            
            # Score: +2 if any service price <= budget_max_rub (if budget provided)
            if budget_max is not None:
                services = Service.query.filter(
                    Service.nutritionist_id == n.nutritionist_id,
                    Service.is_active == True,  # noqa: E712
                ).all()
                
                has_affordable = any(s.price_rub <= budget_max for s in services)
                if has_affordable:
                    score += 2
                    matched_reasons.append("В пределах бюджета")
            
            # Score: +1 if help_mode matches service_type (inferred from title)
            if help_mode:
                services = Service.query.filter(
                    Service.nutritionist_id == n.nutritionist_id,
                    Service.is_active == True,  # noqa: E712
                ).all()
                
                keywords = HELP_MODE_KEYWORDS.get(help_mode, [])
                for service in services:
                    title_lower = (service.title or "").lower()
                    if any(kw in title_lower for kw in keywords):
                        score += 1
                        mode_labels = {
                            "one_time": "Разовая консультация",
                            "plan": "План питания",
                            "long_term": "Длительное сопровождение",
                        }
                        matched_reasons.append(
                            f"Формат: {mode_labels.get(help_mode, _label_for(help_mode))}"
                        )
                        break
            
            # Add rating bonus (0.5 per rating point)
            if n.rating:
                score += float(n.rating) * 0.5
            
            results.append({
                "nutritionist": n,
                "score": round(score, 1),
                "matched_reasons": matched_reasons[:4],  # Limit to 4 reasons
            })
        
        # Sort by score desc, then rating desc
        results.sort(
            key=lambda x: (x["score"], float(x["nutritionist"].rating or 0)),
            reverse=True,
        )
        
        return results[:limit]
