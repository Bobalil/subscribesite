import uuid

from sqlalchemy.orm import Session

from .models import LedgerEntry, TxType, Wallet


def get_or_create_wallet(db: Session, user_id: int) -> Wallet:
    wallet = db.query(Wallet).filter(Wallet.user_id == user_id).first()
    if not wallet:
        wallet = Wallet(user_id=user_id, balance=0)
        db.add(wallet)
        db.flush()
    return wallet


def apply_entry(db: Session, user_id: int, amount: int, entry_type: TxType, description: str = "",
                tx_id: str | None = None) -> LedgerEntry:
    """Атомарно меняет баланс и пишет запись в ledger. amount в копейках, может быть отрицательным."""
    wallet = get_or_create_wallet(db, user_id)
    new_balance = wallet.balance + amount
    if new_balance < 0:
        raise ValueError("INSUFFICIENT_FUNDS")
    wallet.balance = new_balance
    entry = LedgerEntry(
        tx_id=tx_id or uuid.uuid4().hex,
        user_id=user_id,
        entry_type=entry_type,
        amount=amount,
        description=description,
    )
    db.add(entry)
    db.flush()
    return entry