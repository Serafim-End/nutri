"""
Session Tracking Service
Logs user sessions and flags booking/payment activity per session.
"""

from datetime import datetime

from app.extensions import db
from app.models import UserSession


def log_user_session(profile_id: str, source: str) -> UserSession:
    session = UserSession(
        profile_id=profile_id,
        source=source,
        started_at=datetime.utcnow(),
    )
    db.session.add(session)
    db.session.commit()
    return session


def _latest_session(profile_id: str) -> UserSession | None:
    return (
        UserSession.query.filter_by(profile_id=profile_id)
        .order_by(UserSession.started_at.desc())
        .first()
    )


def mark_booking_made(profile_id: str) -> None:
    session = _latest_session(profile_id)
    if not session:
        return
    if not session.booking_made:
        session.booking_made = True
        db.session.commit()


def mark_payment_made(profile_id: str) -> None:
    session = _latest_session(profile_id)
    if not session:
        return
    if not session.payment_made or not session.booking_made:
        session.payment_made = True
        session.booking_made = True
        db.session.commit()
