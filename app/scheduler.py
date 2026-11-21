from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from .ledger import apply_entry
from .models import ExecutionMode, PaymentStatus, Payout, TxType, UserSubscription


def run_due_charges(db: Session) -> dict:
    """Списывает с кошелька пользователя все активные подписки, у которых наступила дата.
    Возвращает сводку. Вызывается по cron/вручную из админки."""
    now = datetime.utcnow()
    due = db.query(UserSubscription).filter(
        UserSubscription.is_active == True,  # noqa: E712
        UserSubscription.next_charge_at <= now,
    ).all()

    summary = {"charged": 0, "failed": 0, "total": 0}
    for sub in due:
        price = sub.service.price
        try:
            apply_entry(db, sub.user_id, -price, TxType.SUBSCRIPTION_PAYMENT,
                        description=f"Оплата подписки {sub.service.name}")
            sub.next_charge_at = now + timedelta(days=30)
            payout = Payout(
                user_id=sub.user_id,
                service_id=sub.service_id,
                amount=price,
                mode=sub.service.execution_mode,
                status=PaymentStatus.PENDING,
                reference=sub.service.payout_details,
            )
            db.add(payout)
            summary["charged"] += 1
            summary["total"] += price
        except ValueError:
            summary["failed"] += 1
    db.commit()
    return summary