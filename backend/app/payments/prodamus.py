"""
Prodamus Payform Payment Provider
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import urlencode, urlparse, parse_qsl
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from flask import current_app

from app.payments.base import PaymentProvider, PaymentIntent, PaymentResult, PaymentStatus

logger = logging.getLogger(__name__)


def _normalize_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _normalize_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_normalize_value(v) for v in value]
    if value is None:
        return ""
    return str(value)


def _sort_object(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _sort_object(value[k]) for k in sorted(value.keys())}
    if isinstance(value, list):
        return [_sort_object(v) for v in value]
    return value


def _signature_payload(data: dict) -> str:
    normalized = _normalize_value(data)
    sorted_data = _sort_object(normalized)
    json_payload = json.dumps(sorted_data, ensure_ascii=False, separators=(",", ":"))
    return json_payload.replace("/", "\\/")


def _sign(data: dict, secret: str) -> str:
    payload = _signature_payload(data)
    return hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()


def _add_query_param(url: str, key: str, value: str) -> str:
    parsed = urlparse(url)
    params = dict(parse_qsl(parsed.query))
    params[key] = value
    new_query = urlencode(params)
    return parsed._replace(query=new_query).geturl()


def _format_expire_msk(minutes: int) -> str:
    expires_at = datetime.now(ZoneInfo("Europe/Moscow")) + timedelta(minutes=minutes)
    return expires_at.strftime("%d.%m.%Y %H:%M")


def _flatten_form_data(data: dict) -> list[tuple[str, str]]:
    items: list[tuple[str, str]] = []

    def walk(prefix: str, value: Any) -> None:
        if isinstance(value, dict):
            for key, val in value.items():
                new_prefix = f"{prefix}[{key}]" if prefix else str(key)
                walk(new_prefix, val)
            return
        if isinstance(value, list):
            for idx, val in enumerate(value):
                new_prefix = f"{prefix}[{idx}]" if prefix else str(idx)
                walk(new_prefix, val)
            return
        items.append((prefix, str(value)))

    walk("", data)
    return items


def _extract_payment_link(payload: Any) -> str | None:
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, dict):
        for key in ("payment_link", "link", "url", "payment_url", "pay_url"):
            value = payload.get(key)
            if isinstance(value, str) and value.startswith("http"):
                return value
        for value in payload.values():
            if isinstance(value, dict):
                nested = _extract_payment_link(value)
                if nested:
                    return nested
    return None


class ProdamusPaymentProvider(PaymentProvider):
    @property
    def name(self) -> str:
        return "prodamus"

    def create_payment_intent(self, booking: Any) -> PaymentIntent:
        config = current_app.config
        form_url = config.get("PAYFORM_FORM_URL") or ""
        secret = config.get("PAYFORM_SECRET") or ""
        sys_code = config.get("PAYFORM_SYS") or ""
        success_url = config.get("PAYFORM_SUCCESS_URL") or ""
        return_url = config.get("PAYFORM_RETURN_URL") or ""
        notification_url = config.get("PAYFORM_NOTIFICATION_URL") or ""
        expire_minutes = int(config.get("PAYFORM_LINK_EXPIRE_MINUTES", 15))

        if not form_url or not secret or not sys_code:
            raise ValueError("PAYFORM_FORM_URL, PAYFORM_SECRET, and PAYFORM_SYS are required")

        booking_id = str(booking.id)
        service_name = booking.service.title if booking.service else "Услуга"

        success_url = _add_query_param(success_url, "order_id", booking_id)
        return_url = _add_query_param(return_url, "order_id", booking_id)

        data: dict[str, Any] = {
            "order_id": booking_id,
            "order_num": booking_id,
            "products": [
                {
                    "name": service_name,
                    "price": booking.price_rub,
                    "quantity": 1,
                    "type": "service",
                }
            ],
            "do": "link",
            "sys": sys_code,
            "currency": "rub",
            "urlSuccess": success_url,
            "urlReturn": return_url,
            "urlNotification": notification_url,
            "type": "json",
            "callbackType": "json",
            "link_expired": _format_expire_msk(expire_minutes),
        }

        signature = _sign(data, secret)
        data["signature"] = signature

        post_items = _flatten_form_data(data)
        encoded = urlencode(post_items).encode("utf-8")

        form_url = form_url if form_url.endswith("/") else f"{form_url}/"
        req = Request(form_url, data=encoded, method="POST")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")

        with urlopen(req, timeout=15) as response:
            raw_body = response.read().decode("utf-8").strip()

        payment_url = None
        try:
            parsed = json.loads(raw_body)
            payment_url = _extract_payment_link(parsed)
        except json.JSONDecodeError:
            payment_url = _extract_payment_link(raw_body)

        if not payment_url:
            logger.error(
                "[Prodamus] Failed to parse payment link response: %s",
                raw_body[:500],
            )
            raise ValueError("Failed to create payment link")

        expires_at = booking.slot.hold_expires_at.isoformat() if booking.slot else None
        payment_id = str(booking.payment.id) if booking.payment else booking_id

        return PaymentIntent(
            payment_id=payment_id,
            provider=self.name,
            payment_url=payment_url,
            amount_rub=booking.price_rub,
            currency=booking.currency,
            expires_at=expires_at,
        )

    def handle_webhook(self, payload: dict, headers: dict) -> PaymentResult:
        payment_status = str(payload.get("payment_status", "")).lower()
        booking_id = self._extract_booking_id(payload)

        if not booking_id:
            raise ValueError("order_id is required in webhook payload")

        status = (
            PaymentStatus.SUCCEEDED
            if payment_status == "success"
            else PaymentStatus.FAILED
        )

        provider_payment_id = (
            str(payload.get("order_id"))
            if payload.get("order_id")
            else f"prodamus_{booking_id}"
        )

        logger.info(
            "[Prodamus] Webhook processed: booking_id=%s status=%s",
            booking_id,
            status.value,
        )

        return PaymentResult(
            booking_id=str(booking_id),
            provider_payment_id=provider_payment_id,
            status=status,
            raw_payload=payload,
        )

    @staticmethod
    def _extract_booking_id(payload: dict) -> str | None:
        for key in ("order_num", "order_id", "booking_id"):
            value = payload.get(key)
            if isinstance(value, str) and ProdamusPaymentProvider._is_uuid(value):
                return value
        return None

    @staticmethod
    def _is_uuid(value: str) -> bool:
        try:
            uuid.UUID(value)
            return True
        except ValueError:
            return False

    def verify_signature(self, payload: dict, headers: dict) -> bool:
        secret = current_app.config.get("PAYFORM_SECRET") or ""
        if not secret:
            logger.warning("[Prodamus] PAYFORM_SECRET is not set")
            return False

        signature = headers.get("Sign") or headers.get("sign") or headers.get("SIGN")
        if not signature:
            return False

        expected = _sign(payload, secret)
        return hmac.compare_digest(expected, signature)
