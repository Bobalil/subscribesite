from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_admin_user
from ..models import LedgerEntry, Payout, Service, User
from ..scheduler import run_due_charges

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request, admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    users = db.query(User).all()
    services = db.query(Service).all()
    payouts = db.query(Payout).order_by(Payout.id.desc()).limit(50).all()
    ledger = db.query(LedgerEntry).order_by(LedgerEntry.id.desc()).limit(50).all()
    return templates.TemplateResponse("admin.html", {
        "request": request, "admin": admin, "users": users, "services": services,
        "payouts": payouts, "ledger": ledger
    })


@router.post("/admin/run-charges")
def run_charges(admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    run_due_charges(db)
    return RedirectResponse("/admin", status_code=303)