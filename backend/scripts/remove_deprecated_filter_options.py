#!/usr/bin/env python3
"""
Remove deprecated tag/filter values from JSON fields.
Targets nutritionist tags/specializations, client filters, and intake answers.
"""

import os
import sys
from typing import Iterable

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models import NutritionistProfile, ClientFilterState, Intake


DEPRECATED_VALUES = {
    "keto",
    "intermittent_fasting",
    "detox",
    "anti_aging",
    "anti_age",
    "anti-age",
}


def _clean_list(values: Iterable[str]) -> list[str]:
    return [v for v in values if v not in DEPRECATED_VALUES]


def remove_deprecated_values() -> None:
    app = create_app()
    with app.app_context():
        profiles_updated = 0
        filters_updated = 0
        intakes_updated = 0

        for profile in NutritionistProfile.query.all():
            updated = False
            if profile.tags:
                cleaned = _clean_list(profile.tags)
                if cleaned != profile.tags:
                    profile.tags = cleaned
                    updated = True
            if profile.specializations:
                cleaned = _clean_list(profile.specializations)
                if cleaned != profile.specializations:
                    profile.specializations = cleaned
                    updated = True
            if updated:
                profiles_updated += 1

        for state in ClientFilterState.query.all():
            filters = state.filters or {}
            updated = False
            for key in ("goals", "topics", "dietary", "specializations", "tags"):
                if isinstance(filters.get(key), list):
                    cleaned = _clean_list(filters[key])
                    if cleaned != filters[key]:
                        filters[key] = cleaned
                        updated = True
            if updated:
                state.filters = filters
                filters_updated += 1

        for intake in Intake.query.all():
            answers = intake.answers or {}
            updated = False
            for key in ("goals", "dietary_restrictions", "health_conditions"):
                if isinstance(answers.get(key), list):
                    cleaned = _clean_list(answers[key])
                    if cleaned != answers[key]:
                        answers[key] = cleaned
                        updated = True
            if updated:
                intake.answers = answers
                intakes_updated += 1

        db.session.commit()
        print(f"Updated nutritionist profiles: {profiles_updated}")
        print(f"Updated client filter states: {filters_updated}")
        print(f"Updated intakes: {intakes_updated}")


if __name__ == "__main__":
    remove_deprecated_values()
