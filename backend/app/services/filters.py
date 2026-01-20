"""
Filters Service
Functions for normalizing intake answers to search filters.
"""

from typing import Dict, List, Optional, Any


# Available filter options (used by frontend and backend)
FILTER_OPTIONS = {
    "goals": [
        {"id": "weight_loss", "label": "Снижение веса"},
        {"id": "muscle_gain", "label": "Набор массы"},
        {"id": "better_nutrition", "label": "Здоровое питание"},
        {"id": "gut_health", "label": "Здоровье ЖКТ"},
        {"id": "sports_nutrition", "label": "Спортивное питание"},
        {"id": "pregnancy", "label": "Питание при беременности/кормлении"},
        {"id": "pediatric_nutrition", "label": "Детское питание (работа с родителями)"},
        {"id": "other", "label": "Другое"},
    ],
    "topics": [
        {"id": "nutrition_basics", "label": "Основы питания"},
        {"id": "meal_planning", "label": "Планирование рациона"},
        {"id": "supplements", "label": "Добавки и витамины"},
        {"id": "weight_management", "label": "Контроль веса"},
        {"id": "sports_performance", "label": "Спортивные результаты"},
        {"id": "chronic_conditions", "label": "Хронические заболевания"},
        {"id": "eating_disorders", "label": "Расстройства пищевого поведения"},
        {"id": "pediatric_nutrition", "label": "Детское питание"},
    ],
    "dietary": [
        {"id": "vegetarian", "label": "Вегетарианство"},
        {"id": "vegan", "label": "Веганство"},
        {"id": "gluten_free", "label": "Без глютена"},
        {"id": "lactose_free", "label": "Без лактозы"},
        {"id": "halal", "label": "Халяль"},
        {"id": "kosher", "label": "Кошер"},
    ],
    "help_modes": [
        {"id": "one_time", "label": "Разовая консультация"},
        {"id": "plan", "label": "План питания"},
        {"id": "long_term", "label": "Длительное сопровождение"},
    ],
    "budget_ranges": [
        {"id": "up_to_2000", "max": 2000, "label": "До 2 000 ₽"},
        {"id": "2000_3000", "max": 3000, "label": "2 000 – 3 000 ₽"},
        {"id": "3000_5000", "max": 5000, "label": "3 000 – 5 000 ₽"},
        {"id": "above_5000", "max": None, "label": "От 5 000 ₽"},
        {"id": "unknown", "max": None, "label": "Не знаю"},
    ],
}


def get_empty_filters() -> Dict[str, Any]:
    """Return empty/default filter structure."""
    return {
        "goals": [],
        "topics": [],
        "budget_max_rub": None,
        "dietary": [],
        "help_mode": None,
        "specializations": [],
        "tags": [],
    }


def normalize_filters_from_intake(answers: Dict[str, Any]) -> Dict[str, Any]:
    """
    Translate onboarding intake answers into search filters.
    
    Args:
        answers: Raw intake answers from the questionnaire
        
    Returns:
        Normalized filters dict with stable key names
    """
    filters = get_empty_filters()
    
    # Map goals directly (they match specializations)
    goals = answers.get("goals", [])
    if isinstance(goals, list):
        filters["goals"] = [g for g in goals if isinstance(g, str)]
        # Goals also become specializations for matching
        filters["specializations"] = filters["goals"].copy()
    
    # Map dietary restrictions
    dietary = answers.get("dietary_restrictions", [])
    if isinstance(dietary, list):
        # Filter out "none" as it's not a real restriction
        filters["dietary"] = [d for d in dietary if isinstance(d, str) and d != "none"]
        # Dietary also becomes tags for matching
        filters["tags"] = filters["dietary"].copy()
    
    # Map budget - use budget_max if available
    budget_max = answers.get("budget_max")
    if budget_max is not None and isinstance(budget_max, (int, float)):
        filters["budget_max_rub"] = int(budget_max)
    
    # Map preferred schedule to help_mode
    # This is a heuristic mapping based on schedule preferences
    schedule = answers.get("preferred_schedule")
    if schedule == "flexible":
        filters["help_mode"] = "long_term"
    elif schedule in ("weekdays", "evenings"):
        filters["help_mode"] = "plan"
    elif schedule == "weekends":
        filters["help_mode"] = "one_time"
    
    # Add health conditions to specializations
    health_conditions = answers.get("health_conditions", [])
    if isinstance(health_conditions, list):
        for condition in health_conditions:
            if isinstance(condition, str) and condition not in filters["specializations"]:
                filters["specializations"].append(condition)
    
    return filters


def validate_filters(filters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and sanitize filter values.
    
    Args:
        filters: Raw filters from client
        
    Returns:
        Validated filters dict with proper types
    """
    validated = get_empty_filters()
    
    # Validate goals (list of strings)
    if isinstance(filters.get("goals"), list):
        valid_goal_ids = {g["id"] for g in FILTER_OPTIONS["goals"]}
        validated["goals"] = [
            g for g in filters["goals"] 
            if isinstance(g, str) and g in valid_goal_ids
        ]
    
    # Validate topics (list of strings)
    if isinstance(filters.get("topics"), list):
        valid_topic_ids = {t["id"] for t in FILTER_OPTIONS["topics"]}
        validated["topics"] = [
            t for t in filters["topics"] 
            if isinstance(t, str) and t in valid_topic_ids
        ]
    
    # Validate dietary (list of strings)
    if isinstance(filters.get("dietary"), list):
        valid_dietary_ids = {d["id"] for d in FILTER_OPTIONS["dietary"]}
        validated["dietary"] = [
            d for d in filters["dietary"] 
            if isinstance(d, str) and d in valid_dietary_ids
        ]
    
    # Validate budget_max_rub (int or null)
    budget = filters.get("budget_max_rub")
    if budget is not None:
        try:
            validated["budget_max_rub"] = int(budget) if int(budget) > 0 else None
        except (ValueError, TypeError):
            validated["budget_max_rub"] = None
    
    # Validate help_mode (string from enum or null)
    help_mode = filters.get("help_mode")
    valid_help_modes = {m["id"] for m in FILTER_OPTIONS["help_modes"]}
    if help_mode in valid_help_modes:
        validated["help_mode"] = help_mode
    
    # Validate specializations (list of strings, any values allowed)
    if isinstance(filters.get("specializations"), list):
        validated["specializations"] = [
            s for s in filters["specializations"] 
            if isinstance(s, str)
        ]
    
    # Validate tags (list of strings, any values allowed)
    if isinstance(filters.get("tags"), list):
        validated["tags"] = [
            t for t in filters["tags"] 
            if isinstance(t, str)
        ]
    
    return validated
