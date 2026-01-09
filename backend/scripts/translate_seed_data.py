#!/usr/bin/env python3
"""
Update seeded nutritionists and services to Russian text.
Targets only known seed users by telegram_user_id.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models import Profile, Service


SEED_TRANSLATIONS = {
    200000001: {
        "full_name": "Елена Петрова",
        "bio": (
            "Сертифицированный клинический нутрициолог с 10-летним опытом. "
            "Специализируется на контроле веса, диабете и спортивном питании."
        ),
        "services": {
            "Initial Consultation": {
                "title": "Первичная консультация",
                "description": "Комплексная 60‑минутная оценка ваших целей, "
                               "пищевых привычек и разработка персонального плана питания.",
            },
            "Follow-up Session": {
                "title": "Повторная консультация",
                "description": "30‑минутная проверка прогресса и корректировка плана.",
            },
        },
    },
    200000002: {
        "full_name": "Михаил Чен, RD",
        "bio": (
            "Дипломированный диетолог, специализирующийся на растительном питании и "
            "холистическом подходе. Помогаю клиентам находить баланс через осознанное питание."
        ),
        "services": {
            "Wellness Consultation": {
                "title": "Консультация по благополучию",
                "description": "Холистическая 45‑минутная сессия о питании и балансе образа жизни.",
            },
            "Plant-Based Transition": {
                "title": "Переход на растительное питание",
                "description": "Полный гид по переходу на растительный рацион. "
                               "Включает планирование питания и подбор рецептов.",
            },
        },
    },
    200000003: {
        "full_name": "Анна Соколова",
        "bio": (
            "Специалист по спортивному питанию с опытом 8 лет. Бывший нутрициолог "
            "олимпийской сборной. Помогаю спортсменам достигать пика формы через оптимальное питание."
        ),
        "services": {
            "Sports Performance Consultation": {
                "title": "Консультация по спортивной эффективности",
                "description": "Комплексная оценка питания для спортсменов. "
                               "Включает анализ состава тела и персональные стратегии питания.",
            },
            "Athlete Meal Plan": {
                "title": "План питания для спортсмена",
                "description": "Индивидуальный недельный план питания под график тренировок и цели соревнований.",
            },
            "Pre-Competition Strategy": {
                "title": "Стратегия перед соревнованиями",
                "description": "Оптимизация питания для максимальной формы в день старта.",
            },
        },
    },
    200000004: {
        "full_name": "Мария Иванова, PhD",
        "bio": (
            "PhD в области нутрициологии. Научный подход к здоровью ЖКТ и пищеварения. "
            "Автор публикаций и лектор."
        ),
        "services": {
            "Gut Health Assessment": {
                "title": "Оценка здоровья ЖКТ",
                "description": "Комплексная оценка состояния ЖКТ с персональными рекомендациями.",
            },
            "IBS Management Program": {
                "title": "Программа по управлению СРК",
                "description": "6-недельная программа контроля симптомов СРК через питание и образ жизни.",
            },
            "Follow-up Consultation": {
                "title": "Повторная консультация",
                "description": "Проверка прогресса и корректировка плана.",
            },
        },
    },
    200000005: {
        "full_name": "Алексей Волков",
        "bio": (
            "Сертифицированный нутрициолог, специализирующийся на диабете и метаболическом здоровье. "
            "12 лет клинической практики."
        ),
        "services": {
            "Diabetes Nutrition Consultation": {
                "title": "Консультация по питанию при диабете",
                "description": "Персональный план питания для контроля сахара в крови.",
            },
            "Metabolic Health Assessment": {
                "title": "Оценка метаболического здоровья",
                "description": "Комплексная оценка метаболического здоровья с планом действий.",
            },
            "Monthly Support Session": {
                "title": "Ежемесячная поддержка",
                "description": "Регулярное сопровождение при диабете.",
            },
        },
    },
    200000006: {
        "full_name": "Ольга Кузнецова",
        "bio": (
            "Специалист по питанию при беременности и в детском возрасте. "
            "Помогаю семьям сформировать здоровые пищевые привычки."
        ),
        "services": {
            "Pregnancy Nutrition Plan": {
                "title": "План питания при беременности",
                "description": "Рекомендации по питанию по триместрам для здоровой беременности.",
            },
            "Postpartum & Breastfeeding": {
                "title": "Послеродовой период и ГВ",
                "description": "Поддержка питания для молодых мам и грудного вскармливания.",
            },
            "Pediatric Nutrition Consultation": {
                "title": "Консультация по детскому питанию",
                "description": "Питание по возрасту для детей и младенцев.",
            },
        },
    },
    200000007: {
        "full_name": "Дмитрий Новиков",
        "bio": (
            "Эксперт по доступному питанию. Доказываю, что здоровое питание может быть бюджетным. "
            "Специалист по заготовкам."
        ),
        "services": {
            "Budget Nutrition Consultation": {
                "title": "Бюджетная консультация по питанию",
                "description": "Как питаться полезно при любом бюджете.",
            },
            "Meal Prep Masterclass": {
                "title": "Мастер‑класс по заготовкам",
                "description": "Стратегии еженедельных заготовок, экономящие время и деньги.",
            },
            "Quick Check-in": {
                "title": "Короткий чек‑ин",
                "description": "15‑минутная проверка прогресса и рекомендации.",
            },
        },
    },
    200000008: {
        "full_name": "Виктория Смирнова",
        "bio": (
            "Холистический нутрициолог, сочетающий восточные и западные подходы. "
            "Сертифицирована в аюрведическом питании и функциональной медицине."
        ),
        "services": {
            "Holistic Health Assessment": {
                "title": "Холистическая оценка здоровья",
                "description": "Оценка тела, психики и питания с персональным планом оздоровления.",
            },
            "Ayurvedic Consultation": {
                "title": "Аюрведическая консультация",
                "description": "Определение доши и персональные рекомендации по питанию.",
            },
            "Stress & Nutrition Session": {
                "title": "Питание и стресс",
                "description": "Как питание влияет на психическое здоровье и управление стрессом.",
            },
        },
    },
}


def translate_seed_data() -> None:
    app = create_app()
    with app.app_context():
        updated_profiles = 0
        updated_services = 0

        for telegram_id, data in SEED_TRANSLATIONS.items():
            profile = Profile.query.filter_by(telegram_user_id=telegram_id).first()
            if not profile:
                continue

            if data.get("full_name") and profile.full_name != data["full_name"]:
                profile.full_name = data["full_name"]
                updated_profiles += 1

            if profile.nutritionist_profile and data.get("bio"):
                profile.nutritionist_profile.bio = data["bio"]
                updated_profiles += 1

            services = Service.query.filter_by(nutritionist_id=profile.id).all()
            service_updates = data.get("services", {})
            for service in services:
                if service.title not in service_updates:
                    continue
                update = service_updates[service.title]
                service.title = update["title"]
                service.description = update["description"]
                updated_services += 1

        db.session.commit()
        print(f"Updated profiles: {updated_profiles}")
        print(f"Updated services: {updated_services}")


if __name__ == "__main__":
    translate_seed_data()
