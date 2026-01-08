"""
Swagger/OpenAPI Configuration for NutriMatch API.
Provides interactive API documentation at /apidocs/
"""

SWAGGER_CONFIG = {
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec",
            "route": "/apispec.json",
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/",  # Swagger UI доступен на корневом пути
}

SWAGGER_TEMPLATE = {
    "swagger": "2.0",
    "info": {
        "title": "NutriMatch API",
        "description": """
## 🥗 NutriMatch - Telegram Nutritionists Marketplace

NutriMatch — это платформа для поиска нутрициологов через Telegram Mini App.

### Основные возможности:
- **Аутентификация** через Telegram Mini App
- **Поиск нутрициологов** с фильтрами и скорингом
- **Бронирование** консультаций с оплатой
- **Управление профилем** нутрициолога

### Аутентификация
Большинство эндпоинтов требуют JWT токен в заголовке:
```
Authorization: Bearer <token>
```

Получить токен можно через `/api/auth/telegram/verify` с Telegram initData.

### Режим разработки
В dev-режиме доступен `/api/auth/dev-login` для тестирования без Telegram.
        """,
        "version": "1.0.0",
        "contact": {
            "name": "NutriMatch Support",
            "email": "support@nutrutioncoach.com",
        },
        "license": {
            "name": "Private",
        },
    },
    "host": "api.nutrutioncoach.com",
    "basePath": "/",
    "schemes": ["https", "http"],
    "tags": [
        {
            "name": "Auth",
            "description": "Аутентификация через Telegram",
        },
        {
            "name": "Public",
            "description": "Публичные эндпоинты (без авторизации)",
        },
        {
            "name": "Clients",
            "description": "Эндпоинты для клиентов",
        },
        {
            "name": "Bookings",
            "description": "Бронирование консультаций",
        },
        {
            "name": "Nutritionists",
            "description": "Эндпоинты для нутрициологов",
        },
        {
            "name": "Payments",
            "description": "Обработка платежей",
        },
        {
            "name": "Admin",
            "description": "Административные эндпоинты",
        },
        {
            "name": "Bot",
            "description": "Эндпоинты для Telegram бота",
        },
        {
            "name": "Health",
            "description": "Проверка здоровья сервиса",
        },
    ],
    "securityDefinitions": {
        "BearerAuth": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "JWT токен, полученный через /api/auth/telegram/verify. Формат: Bearer <token>",
        }
    },
    "definitions": {
        # ========== Auth Schemas ==========
        "TelegramAuthRequest": {
            "type": "object",
            "required": ["init_data"],
            "properties": {
                "init_data": {
                    "type": "string",
                    "description": "Telegram Mini App initData string",
                    "example": "query_id=AAHdF6IQAAAAAN0XohDhrOrc&user=%7B%22id%22%3A123456789%7D&hash=abc123",
                }
            },
        },
        "DevLoginRequest": {
            "type": "object",
            "properties": {
                "telegram_user_id": {
                    "type": "integer",
                    "description": "ID пользователя Telegram (по умолчанию: 300000001)",
                    "example": 300000001,
                }
            },
        },
        "AuthResponse": {
            "type": "object",
            "properties": {
                "access_token": {
                    "type": "string",
                    "description": "JWT токен для авторизации",
                    "example": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                },
                "token_type": {
                    "type": "string",
                    "enum": ["bearer"],
                    "example": "bearer",
                },
                "profile": {"$ref": "#/definitions/Profile"},
            },
        },
        # ========== Profile Schemas ==========
        "Profile": {
            "type": "object",
            "properties": {
                "id": {"type": "string", "format": "uuid"},
                "telegram_user_id": {"type": "integer", "example": 123456789},
                "role": {
                    "type": "string",
                    "enum": ["client", "nutritionist", "admin"],
                    "example": "client",
                },
                "full_name": {"type": "string", "example": "Иван Иванов"},
                "photo_url": {"type": "string", "x-nullable": True},
                "created_at": {"type": "string", "format": "date-time"},
                "updated_at": {"type": "string", "format": "date-time"},
            },
        },
        # ========== Nutritionist Schemas ==========
        "Nutritionist": {
            "type": "object",
            "properties": {
                "id": {"type": "string", "format": "uuid"},
                "profile_id": {"type": "string", "format": "uuid"},
                "bio": {"type": "string", "example": "Сертифицированный нутрициолог..."},
                "specializations": {
                    "type": "array",
                    "items": {"type": "string"},
                    "example": ["weight_loss", "sports_nutrition"],
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "example": ["vegetarian", "keto"],
                },
                "rating": {"type": "number", "format": "float", "example": 4.85},
                "reviews_count": {"type": "integer", "example": 47},
                "verification_status": {
                    "type": "string",
                    "enum": ["draft", "pending", "approved", "rejected", "needs_update"],
                    "example": "approved",
                },
                "is_active": {"type": "boolean", "example": True},
                "profile": {"$ref": "#/definitions/Profile"},
            },
        },
        "NutritionistUpsertRequest": {
            "type": "object",
            "required": ["telegram_user_id", "full_name"],
            "properties": {
                "telegram_user_id": {"type": "integer", "example": 123456789},
                "full_name": {"type": "string", "example": "Dr. Elena Petrova"},
                "photo_url": {"type": "string", "x-nullable": True},
                "bio": {"type": "string", "example": "Certified nutritionist..."},
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "example": ["vegetarian"],
                },
                "specializations": {
                    "type": "array",
                    "items": {"type": "string"},
                    "example": ["weight_loss", "diabetes"],
                },
                "submit_for_verification": {"type": "boolean", "example": True},
            },
        },
        "NutritionistSearchResult": {
            "type": "object",
            "allOf": [
                {"$ref": "#/definitions/Nutritionist"},
                {
                    "type": "object",
                    "properties": {
                        "score": {
                            "type": "number",
                            "format": "float",
                            "description": "Релевантность по фильтрам (0-10)",
                            "example": 8.5,
                        },
                        "matched_reasons": {
                            "type": "array",
                            "items": {"type": "string"},
                            "example": ["Specializes in weight loss", "Within budget"],
                        },
                    },
                },
            ],
        },
        # ========== Service Schemas ==========
        "Service": {
            "type": "object",
            "properties": {
                "id": {"type": "string", "format": "uuid"},
                "nutritionist_id": {"type": "string", "format": "uuid"},
                "title": {"type": "string", "example": "Первичная консультация"},
                "description": {"type": "string", "example": "60-минутный разбор..."},
                "duration_minutes": {"type": "integer", "example": 60},
                "price_rub": {"type": "integer", "example": 3000},
                "is_active": {"type": "boolean", "example": True},
            },
        },
        "ServiceCreateRequest": {
            "type": "object",
            "required": ["title", "duration_minutes", "price_rub"],
            "properties": {
                "title": {"type": "string", "example": "Initial Consultation"},
                "description": {"type": "string"},
                "duration_minutes": {"type": "integer", "example": 60},
                "price_rub": {"type": "integer", "example": 3000},
                "is_active": {"type": "boolean", "default": True},
            },
        },
        # ========== Slot Schemas ==========
        "Slot": {
            "type": "object",
            "properties": {
                "id": {"type": "string", "format": "uuid"},
                "nutritionist_id": {"type": "string", "format": "uuid"},
                "start_at": {"type": "string", "format": "date-time"},
                "end_at": {"type": "string", "format": "date-time"},
                "status": {
                    "type": "string",
                    "enum": ["free", "held", "booked", "cancelled"],
                    "example": "free",
                },
                "hold_expires_at": {"type": "string", "format": "date-time", "x-nullable": True},
            },
        },
        "SlotCreateRequest": {
            "type": "object",
            "required": ["slots"],
            "properties": {
                "slots": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["start_at", "end_at"],
                        "properties": {
                            "start_at": {"type": "string", "format": "date-time"},
                            "end_at": {"type": "string", "format": "date-time"},
                        },
                    },
                }
            },
        },
        # ========== Booking Schemas ==========
        "Booking": {
            "type": "object",
            "properties": {
                "id": {"type": "string", "format": "uuid"},
                "client_id": {"type": "string", "format": "uuid"},
                "nutritionist_id": {"type": "string", "format": "uuid"},
                "service_id": {"type": "string", "format": "uuid"},
                "slot_id": {"type": "string", "format": "uuid"},
                "status": {
                    "type": "string",
                    "enum": ["pending_payment", "paid", "cancelled", "completed", "no_show", "refunded"],
                    "example": "pending_payment",
                },
                "price_rub": {"type": "integer", "example": 3000},
                "currency": {"type": "string", "example": "RUB"},
                "client_note": {"type": "string", "x-nullable": True},
                "created_at": {"type": "string", "format": "date-time"},
                "paid_at": {"type": "string", "format": "date-time", "x-nullable": True},
            },
        },
        "BookingCreateRequest": {
            "type": "object",
            "required": ["service_id", "slot_id"],
            "properties": {
                "service_id": {"type": "string", "format": "uuid"},
                "slot_id": {"type": "string", "format": "uuid"},
                "client_note": {"type": "string", "x-nullable": True},
            },
        },
        "BookingCreateResponse": {
            "type": "object",
            "properties": {
                "booking": {"$ref": "#/definitions/Booking"},
                "payment": {"$ref": "#/definitions/PaymentIntent"},
            },
        },
        "BookingCancelRequest": {
            "type": "object",
            "properties": {
                "reason": {"type": "string", "example": "Changed my mind"},
            },
        },
        # ========== Payment Schemas ==========
        "PaymentIntent": {
            "type": "object",
            "properties": {
                "payment_id": {"type": "string", "format": "uuid"},
                "provider": {"type": "string", "example": "mock"},
                "payment_url": {"type": "string", "format": "uri"},
                "amount_rub": {"type": "integer", "example": 3000},
                "currency": {"type": "string", "example": "RUB"},
                "expires_at": {"type": "string", "format": "date-time"},
            },
        },
        "PaymentWebhookRequest": {
            "type": "object",
            "required": ["provider", "payment_id", "booking_id", "amount_rub", "status"],
            "properties": {
                "provider": {"type": "string", "example": "telegram"},
                "payment_id": {"type": "string", "example": "provider_payment_123"},
                "booking_id": {"type": "string", "format": "uuid"},
                "amount_rub": {"type": "integer", "example": 3000},
                "status": {
                    "type": "string",
                    "enum": ["succeeded", "failed"],
                    "example": "succeeded",
                },
                "signature": {"type": "string", "description": "HMAC-SHA256 подпись"},
            },
        },
        # ========== Intake Schemas ==========
        "IntakeRequest": {
            "type": "object",
            "properties": {
                "goals": {
                    "type": "array",
                    "items": {"type": "string"},
                    "example": ["weight_loss", "better_nutrition"],
                },
                "dietary_restrictions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "example": ["vegetarian"],
                },
                "budget_min": {"type": "integer", "example": 2000},
                "budget_max": {"type": "integer", "example": 5000},
                "preferred_schedule": {"type": "string", "example": "weekends"},
                "health_conditions": {"type": "array", "items": {"type": "string"}},
                "additional_notes": {"type": "string"},
            },
        },
        "Intake": {
            "type": "object",
            "properties": {
                "id": {"type": "string", "format": "uuid"},
                "client_id": {"type": "string", "format": "uuid"},
                "answers": {"type": "object"},
                "created_at": {"type": "string", "format": "date-time"},
                "updated_at": {"type": "string", "format": "date-time"},
            },
        },
        # ========== Filter Schemas ==========
        "SearchFilters": {
            "type": "object",
            "properties": {
                "goals": {
                    "type": "array",
                    "items": {"type": "string"},
                    "example": ["weight_loss"],
                },
                "topics": {"type": "array", "items": {"type": "string"}},
                "budget_max_rub": {"type": "integer", "example": 5000},
                "dietary": {
                    "type": "array",
                    "items": {"type": "string"},
                    "example": ["vegetarian"],
                },
                "help_mode": {
                    "type": "string",
                    "enum": ["one_time", "regular"],
                    "example": "one_time",
                },
                "specializations": {"type": "array", "items": {"type": "string"}},
                "tags": {"type": "array", "items": {"type": "string"}},
            },
        },
        "FilterOptions": {
            "type": "object",
            "properties": {
                "goals": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "label": {"type": "string"},
                        },
                    },
                },
                "topics": {"type": "array", "items": {"type": "object"}},
                "dietary": {"type": "array", "items": {"type": "object"}},
                "help_modes": {"type": "array", "items": {"type": "object"}},
                "budget_ranges": {"type": "array", "items": {"type": "object"}},
            },
        },
        # ========== Document Schemas ==========
        "Document": {
            "type": "object",
            "properties": {
                "id": {"type": "string", "format": "uuid"},
                "nutritionist_id": {"type": "string", "format": "uuid"},
                "type": {
                    "type": "string",
                    "enum": ["diploma", "certificate", "other"],
                },
                "file_path": {"type": "string"},
                "created_at": {"type": "string", "format": "date-time"},
            },
        },
        "DocumentCreateRequest": {
            "type": "object",
            "required": ["type", "file_path"],
            "properties": {
                "type": {
                    "type": "string",
                    "enum": ["diploma", "certificate", "other"],
                },
                "file_path": {"type": "string"},
            },
        },
        # ========== Admin Schemas ==========
        "AdminRejectRequest": {
            "type": "object",
            "required": ["reason"],
            "properties": {
                "reason": {"type": "string", "example": "Missing required documents"},
            },
        },
        # ========== Common Schemas ==========
        "Error": {
            "type": "object",
            "properties": {
                "error": {"type": "string", "example": "Resource not found"},
                "details": {"type": "array", "items": {"type": "object"}},
            },
        },
        "HealthResponse": {
            "type": "object",
            "properties": {
                "status": {"type": "string", "example": "healthy"},
                "service": {"type": "string", "example": "nutrimatch-api"},
            },
        },
        "DatabaseHealthResponse": {
            "type": "object",
            "properties": {
                "status": {"type": "string", "enum": ["healthy", "unhealthy"]},
                "database": {"type": "string"},
                "connection": {"type": "boolean"},
                "revision": {"type": "string", "x-nullable": True},
                "provider": {"type": "string"},
                "error": {"type": "string", "x-nullable": True},
            },
        },
    },
}
