from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import httpx
from . import models, database
from pydantic import BaseModel, EmailStr

# Создаем таблицы при старте
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="User Service")

# Pydantic схема для создания пользователя
class UserCreate(BaseModel):
    email: EmailStr
    name: str

# Функция для вызова Notification Service
async def send_notification(user_email: str, user_name: str):
    # URL берем из имени сервиса в docker-compose
    notification_url = "http://notification_service:8001/notify"
    payload = {
        "email": user_email,
        "message": f"Добро пожаловать, {user_name}! Спасибо за регистрацию в TaskHub."
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(notification_url, json=payload, timeout=5.0)
            response.raise_for_status()
            print(f"Уведомление для {user_email} отправлено в Notification Service")
        except Exception as e:
            # В реальном приложении здесь должна быть логика повторных попыток (retry)
            print(f"Ошибка при вызове Notification Service: {e}")

@app.post("/users/", response_model=UserCreate)
async def create_user(user: UserCreate, db: Session = Depends(database.get_db)):
    # Проверяем, нет ли уже пользователя с таким email
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email уже зарегистрирован")

    # Создаем пользователя в БД
    db_user = models.User(email=user.email, name=user.name)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # АСИНХРОННО вызываем Notification Service (не блокируем ответ пользователю)
    # Используем asyncio.create_task для фоновой задачи
    import asyncio
    asyncio.create_task(send_notification(user.email, user.name))

    return user

@app.get("/users/")
async def get_users(db: Session = Depends(database.get_db)):
    users = db.query(models.User).all()
    return users

@app.get("/health")
async def health_check():
    return {"status": "User Service is healthy"}