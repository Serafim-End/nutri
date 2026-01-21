"""
Tests for Prodamus payment integration.
"""

import json
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs

from app.models import Profile, NutritionistProfile, Service, AvailabilitySlot, Booking, Payment
from app.services.payments import PaymentService
from app.payments.prodamus import _sign, _flatten_form_data


def _create_booking(session):
    now = datetime.now(timezone.utc)

    nutritionist_profile = Profile(
        telegram_user_id=700000001,
        full_name="Test Nutritionist",
        role="nutritionist",
    )
    session.add(nutritionist_profile)
    session.flush()

    nutritionist = NutritionistProfile(
        nutritionist_id=nutritionist_profile.id,
        verification_status="approved",
        is_active=True,
    )
    session.add(nutritionist)

    service = Service(
        nutritionist_id=nutritionist_profile.id,
        title="Test Service",
        duration_minutes=60,
        price_rub=2500,
        is_active=True,
    )
    session.add(service)
    session.flush()

    slot = AvailabilitySlot(
        nutritionist_id=nutritionist_profile.id,
        start_at=now + timedelta(days=1),
        end_at=now + timedelta(days=1, hours=1),
        status="held",
        hold_expires_at=now + timedelta(minutes=15),
    )
    session.add(slot)
    session.flush()

    client_profile = Profile(
        telegram_user_id=700000002,
        full_name="Test Client",
        role="client",
    )
    session.add(client_profile)
    session.flush()

    booking = Booking(
        client_id=client_profile.id,
        nutritionist_id=nutritionist_profile.id,
        service_id=service.id,
        slot_id=slot.id,
        status="pending_payment",
        price_rub=service.price_rub,
        currency="RUB",
    )
    session.add(booking)
    session.commit()

    return booking, slot


def test_prodamus_create_payment_intent_returns_link(app, session, monkeypatch):
    with app.app_context():
        booking, _ = _create_booking(session)

        app.config.update({
            "PAYMENT_PROVIDER": "prodamus",
            "PAYFORM_FORM_URL": "https://vitakotsarenko.payform.ru/",
            "PAYFORM_SECRET": "test_secret",
            "PAYFORM_SYS": "vitanutri",
            "PAYFORM_SUCCESS_URL": "https://tma.nutrutioncoach.com/payment/success",
            "PAYFORM_RETURN_URL": "https://tma.nutrutioncoach.com/payment/fail",
            "PAYFORM_NOTIFICATION_URL": "https://api.nutrutioncoach.com/api/payments/webhook/prodamus",
            "PAYFORM_LINK_EXPIRE_MINUTES": 15,
        })

        captured = {}

        def fake_urlopen(request, timeout=15):
            captured["data"] = request.data.decode("utf-8")
            payload = json.dumps({"link": "https://payform.ru/u8zDE/"})

            class DummyResponse:
                def __enter__(self):
                    return self

                def __exit__(self, exc_type, exc, tb):
                    return False

                def read(self):
                    return payload.encode("utf-8")

            return DummyResponse()

        monkeypatch.setattr("app.payments.prodamus.urlopen", fake_urlopen)

        intent, error = PaymentService.create_payment_for_booking(
            booking,
            provider_name="prodamus",
        )

        assert error is None
        assert intent["payment_url"] == "https://payform.ru/u8zDE/"

        parsed = parse_qs(captured["data"])
        assert parsed["order_id"][0] == str(booking.id)
        assert parsed["sys"][0] == "vitanutri"
        assert parsed["do"][0] == "link"
        assert parsed["currency"][0] == "rub"
        assert parsed["type"][0] == "json"
        assert parsed["callbackType"][0] == "json"


def test_prodamus_webhook_form_updates_booking(client, app, session):
    with app.app_context():
        booking, slot = _create_booking(session)

        app.config.update({
            "PAYMENT_PROVIDER": "prodamus",
            "PAYFORM_SECRET": "test_secret",
        })

        payload = {
            "order_id": str(booking.id),
            "payment_status": "success",
            "products": [
                {
                    "name": "Test Service",
                    "price": "2500",
                    "quantity": "1",
                }
            ],
        }
        signature = _sign(payload, "test_secret")
        form_data = dict(_flatten_form_data(payload))

        response = client.post(
            "/api/payments/webhook/prodamus",
            data=form_data,
            headers={"Sign": signature},
        )

        assert response.status_code == 200

        session.refresh(booking)
        session.refresh(slot)
        assert booking.status == "paid"
        assert slot.status == "booked"

        payment = Payment.query.filter_by(booking_id=booking.id).first()
        assert payment is not None
        assert payment.status == "succeeded"
