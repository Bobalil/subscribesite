import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..ledger import apply_entry, get_or_create_wallet
from ..models import ExecutionMode, PaymentStatus, Payout, Service, TxType, User, UserSubscription

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/subscriptions", response_class=HTMLResponse)
def subscriptions_page(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    services = db.query(Service).filter(Service.is_active == True).all()  # noqa: E712
    mine = {s.service_id: s for s in db.query(UserSubscription).filter(UserSubscription.user_id == user.id).all()}
    return templates.TemplateResponse("subscriptions.html", {
        "request": request, "user": user, "services": services, "mine": mine
    })


@router.post("/subscriptions/toggle")
def toggle_subscription(service_id: int = Form(...), user: User = Depends(get_current_user),
                        db: Session = Depends(get_db)):
    sub = db.query(UserSubscription).filter(
        UserSubscription.user_id == user.id, UserSubscription.service_id == service_id).first()
    if sub:
        sub.is_active = not sub.is_active
    else:
        sub = UserSubscription(user_id=user.id, service_id=service_id, is_active=True,
                               next_charge_at=datetime.utcnow() + timedelta(days=30))
        db.add(sub)
    db.commit()
    return RedirectResponse("/subscriptions", status_code=303)


@router.post("/subscriptions/pay-all")
def pay_all(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    subs = db.query(UserSubscription).filter(
        UserSubscription.user_id == user.id, UserSubscription.is_active == True).all()  # noqa: E712
    if not subs:
        return RedirectResponse("/?error=empty", status_code=303)
    total = sum(s.service.price for s in subs)
    try:
        apply_entry(db, user.id, -total, TxType.SUBSCRIPTION_PAYMENT,
                    description=f"Оплата {len(subs)} подписок одной транзакцией")
    except ValueError:
        db.rollback()
        return RedirectResponse("/?error=funds", status_code=303)
    now = datetime.utcnow()
    for s in subs:
        s.next_charge_at = now + timedelta(days=30)
        db.add(Payout(user_id=user.id, service_id=s.service_id, amount=s.service.price,
                      mode=s.service.execution_mode, status=PaymentStatus.PENDING,
                      reference=s.service.payout_details))
    db.commit()
    return RedirectResponse("/", status_code=303)