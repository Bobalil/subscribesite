import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .db import Base, engine
from . import models 
from .catalog import seed_services

# Создаем таблицы и заполняем сервисы
Base.metadata.create_all(bind=engine)
try:
    seed_services()
except Exception as e:
    print(f"Ошибка при заполнении БД: {e}")

# Импорты роутеров
from .auth.router import router as auth_router
from .cards.router import router as cards_router
from .consent import router as legal_router
from .currency import router as currency_router

app = FastAPI(title="Сайт подписок")

if os.path.exists("app/static"):
    app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(auth_router)
app.include_router(cards_router)
app.include_router(legal_router)
app.include_router(currency_router)

@app.get("/")
def index():
    return {"status": "ok", "message": "Сайт работает! Перейдите на /auth/register"}