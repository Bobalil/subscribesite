import uuid

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..ledger import apply_entry, get_or_create_wallet
from ..models import LedgerEntry, Payment, PaymentStatus, TxType, User
from ..payments import get_provider

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    wallet = get_or_create_wallet(db, user.id)
    db.commit()
    entries = (db.query(LedgerEntry).filter(LedgerEntry.user_id == user.id)
               .order_by(LedgerEntry.id.desc()).limit(20).all())
    return templates.TemplateResponse("dashboard.html", {
        "request": request, "user": user, "wallet": wallet, "entries": entries
    })


@router.post("/wallet/topup")
def topup(request: Request, amount: int = Form(...), user: User = Depends(get_current_user),
          db: Session = Depends(get_db)):
    if amount <= 0:
        return RedirectResponse("/?error=amount", status_code=303)
    amount_kop = amount * 100
    idem = uuid.uuid4().hex
    payment = Payment(user_id=user.id, amount=amount_kop, idempotency_key=idem,
                      provider=request.app.state.payment_provider_name)
    db.add(payment)
    db.commit()

    provider = get_provider()
    intent = provider.create_payment(
        amount=amount_kop,
        description="Пополнение кошелька подписок",
        return_url=f"{request.base_url}checkout/success/{payment.id}",
        idempotency_key=idem,
    )
    payment.provider_payment_id = intent.provider_payment_id
    db.commit()
    return RedirectResponse(intent.confirmation_url, status_code=303)


@router.get("/checkout/{provider_payment_id}", response_class=HTMLResponse)
def checkout_page(provider_payment_id: str, request: Request):
    return templates.TemplateResponse("checkout.html", {"request": request, "pid": provider_payment_id})


@router.post("/checkout/{provider_payment_id}/confirm")
def checkout_confirm(provider_payment_id: str, user: User = Depends(get_current_user),
                     db: Session = Depends(get_db)):
    payment = db.query(Payment).filter(Payment.provider_payment_id == provider_payment_id).first()
    if not payment or payment.user_id != user.id or payment.status != PaymentStatus.PENDING:
        return RedirectResponse("/?error=payment", status_code=303)
    apply_entry(db, user.id, payment.amount, TxType.TOPUP, description="Пополнение кошелька")
    payment.status = PaymentStatus.SUCCEEDED
    db.commit()
    return RedirectResponse("/", status_code=303)


@router.get("/checkout/success/{payment_id}")
def checkout_success(payment_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    payment = db.query(Payment).filter(Payment.id == payment_id, Payment.user_id == user.id).first()
    if payment and payment.status == PaymentStatus.PENDING:
        apply_entry(db, user.id, payment.amount, TxType.TOPUP, description="Пополнение кошелька (провайдер)")
        payment.status = PaymentStatus.SUCCEEDED
        db.commit()
    return RedirectResponse("/", status_code=303)