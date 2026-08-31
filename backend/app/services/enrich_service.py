"""Post-import recurring and anomaly enrichment."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.anomaly import detect_anomalies
from app.models import RecurringGroup as RecurringGroupModel
from app.models import Transaction as TransactionModel
from app.recurring import Transaction as RecurringTransaction
from app.recurring import detect_recurring, is_active


def enrich_user(session: Session, user_id: UUID, today: date | None = None) -> None:
    """Recompute recurring groups and anomaly flags over a user's full history."""
    transactions = session.scalars(
        select(TransactionModel)
        .where(TransactionModel.user_id == user_id)
        .order_by(TransactionModel.txn_date, TransactionModel.id)
    ).all()
    if today is None:
        today = max((transaction.txn_date for transaction in transactions), default=date.today())
    detected = detect_recurring(
        [
            RecurringTransaction(
                transaction.merchant,
                transaction.txn_date,
                float(transaction.amount),
                str(transaction.category),
            )
            for transaction in transactions
        ],
        today=today,
    )

    existing = {
        (group.merchant, str(group.cadence)): group
        for group in session.scalars(
            select(RecurringGroupModel).where(RecurringGroupModel.user_id == user_id)
        ).all()
    }
    detected_keys = {(group.merchant, group.cadence) for group in detected}
    for transaction in transactions:
        transaction.is_recurring = False
        transaction.recurring_group_id = None
        transaction.is_anomaly = False
        transaction.anomaly_reason = None
    session.flush()
    for key, existing_group in existing.items():
        if key not in detected_keys:
            session.delete(existing_group)
        else:
            existing_group.active = False

    for detected_group in detected:
        key = (detected_group.merchant, detected_group.cadence)
        record = existing.get(key)
        if record is None:
            record = RecurringGroupModel(
                user_id=user_id, merchant=detected_group.merchant, cadence=key[1]
            )
            session.add(record)
            existing[key] = record
        record.avg_amount = Decimal(str(detected_group.avg_amount)).quantize(Decimal("0.01"))
        record.amount_stddev = Decimal(str(detected_group.amount_stddev)).quantize(Decimal("0.01"))
        record.first_seen = detected_group.first_seen
        record.last_seen = detected_group.last_seen
        record.next_expected = detected_group.next_expected
        record.active = is_active(detected_group, today=today)
        session.flush()
        for transaction in transactions:
            if transaction.merchant == detected_group.merchant:
                transaction.is_recurring = True
                transaction.recurring_group_id = record.id

    non_recurring = [transaction for transaction in transactions if not transaction.is_recurring]
    flags = detect_anomalies(
        [float(transaction.amount) for transaction in non_recurring],
        [str(transaction.category) for transaction in non_recurring],
        [transaction.merchant for transaction in non_recurring],
    )
    for flag in flags:
        transaction = non_recurring[flag.index]
        transaction.is_anomaly = True
        transaction.anomaly_reason = flag.reason
    session.commit()
