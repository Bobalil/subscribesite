from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from ..database import get_db
from ..ledger import apply_entry
from ..models import Payment, PaymentStatus, TxType

router = APIRouter()


@router.post("/webhooks/yookassa")
async def yookassa_webhook(request: Request, db: Session = Depends(get_db)):
    """Вебхук ЮKassa: подтверждаем платёж и зачисляем на кошелёк."""
    data = await request.json()
    event = data.get("event")
    obj = data.get("object", {})
    pid = obj.get("id")
    if event == "payment.succeeded" and pid:
        payment = db.query(Payment).filter(Payment.provider_payment_id == pid).first()
        if payment and payment.status == PaymentStatus.PENDING:
            apply_entry(db, payment.user_id, payment.amount, TxType.TOPUP,
                        description="Пополнение кошелька (webhook)")
            payment.status = PaymentStatus.SUCCEEDED
            db.commit()
    return {"ok": True}