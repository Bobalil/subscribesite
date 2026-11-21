from sqlalchemy.orm import Session
from .models import Service, ExecutionMode
from .db import SessionLocal

def seed_services():
    """Заполняет базу начальными сервисами. Вызывается без аргументов."""
    db: Session = SessionLocal()
    try:
        # Если сервисы уже есть, ничего не делаем
        if db.query(Service).count() > 0:
            return
        
        services = [
            Service(name="Яндекс Плюс", price=399.00, execution_mode=ExecutionMode.LINK),
            Service(name="Netflix", price=1200.00, execution_mode=ExecutionMode.MANUAL),
            Service(name="Spotify", price=299.00, execution_mode=ExecutionMode.MANUAL),
        ]
        db.add_all(services)
        db.commit()
        print("База данных успешно заполнена тестовыми сервисами!")
    except Exception as e:
        print(f"Ошибка в seed_services: {e}")
        db.rollback()
    finally:
        db.close()