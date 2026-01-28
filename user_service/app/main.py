from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import httpx
from . import models, database
from pydantic import BaseModel, EmailStr
import asyncio
import sys
import logging

# Настройка логирования в файл
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/app/user_service.log'),
        logging.StreamHandler() 
    ]
)

logger = logging.getLogger(__name__)


# Принудительно сбрасываем буфер вывода
import functools
print = functools.partial(print, flush=True)

# Создаем таблицы при старте
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="User Service")

# Pydantic схема для создания пользователя
class UserCreate(BaseModel):
    email: EmailStr
    name: str

# Функция для вызова Notification Service с механизмом retry
async def send_notification(user_email: str, user_name: str):
    """Отправка уведомления с механизмом повторных попыток"""
    print(f"\n🚀 [USER SERVICE] Начинаю отправку уведомления для {user_email}")
    
    max_retries = 3
    notification_url = "http://notification_service:8001/notify"
    payload = {
        "email": user_email,
        "message": f"Добро пожаловать, {user_name}! Спасибо за регистрацию в TaskHub."
    }
    
    for attempt in range(1, max_retries + 1):
        try:
            print(f"📤 [USER SERVICE] Попытка {attempt}/{max_retries} отправки уведомления для {user_email}")
            
            # Создаем клиент с явным указанием таймаута
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(notification_url, json=payload)
                response.raise_for_status()
                
            print(f"✅ [USER SERVICE] Уведомление для {user_email} успешно отправлено!")
            return True
            
        except (httpx.ConnectError, httpx.ConnectTimeout) as e:
            print(f"❌ [USER SERVICE] Ошибка подключения при попытке {attempt}: {e}")
            
            if attempt == max_retries:
                print(f"🚫 [USER SERVICE] Достигнут лимит {max_retries} попыток!")
                print(f"⚠️  [USER SERVICE] Сообщение для {user_email} не удалось отправить")
                return False
            else:
                # Экспоненциальная задержка перед следующей попыткой
                delay = 2 ** attempt  # 2, 4, 8 секунд
                print(f"⏱️  [USER SERVICE] Жду {delay} сек. перед повторной попыткой...")
                await asyncio.sleep(delay)
                
        except httpx.HTTPStatusError as e:
            print(f"❌ [USER SERVICE] HTTP ошибка {e.response.status_code} при попытке {attempt}")
            
            if attempt == max_retries:
                print(f"🚫 [USER SERVICE] Достигнут лимит {max_retries} попыток")
                return False
            else:
                delay = 2 ** attempt
                print(f"⏱️  [USER SERVICE] Жду {delay} сек. перед повторной попыткой...")
                await asyncio.sleep(delay)
                
        except Exception as e:
            print(f"❌ [USER SERVICE] Неожиданная ошибка при попытке {attempt}: {type(e).__name__}: {e}")
            
            if attempt == max_retries:
                print(f"🚫 [USER SERVICE] Достигнут лимит {max_retries} попыток")
                return False
            else:
                delay = 2 ** attempt
                print(f"⏱️  [USER SERVICE] Жду {delay} сек. перед повторной попыткой...")
                await asyncio.sleep(delay)
    
    return False

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

    # СНАЧАЛА выводим сообщение о начале процесса
    print(f"\n🎯 [USER SERVICE] Создан пользователь {user.name} ({user.email})")
    print(f"🔗 [USER SERVICE] Начинаю отправку уведомления...")
    
    # АСИНХРОННО вызываем Notification Service с механизмом retry
    # Используем asyncio.ensure_future для надежности
    task = asyncio.ensure_future(send_notification(user.email, user.name))
    
    # Не ждем завершения задачи, но добавляем обработчик ошибок
    def log_result(task):
        try:
            result = task.result()
            if result:
                print(f"✅ [USER SERVICE] Фоновая задача отправки уведомления завершена успешно")
            else:
                print(f"⚠️  [USER SERVICE] Фоновая задача отправки уведомления завершена с ошибкой")
        except Exception as e:
            print(f"❌ [USER SERVICE] Исключение в фоновой задаче: {e}")
    
    task.add_done_callback(log_result)

    return user

@app.post("/test-retry/")
async def test_retry():
    """Тестовый эндпоинт для демонстрации retry механизма"""
    test_email = "retry_test@example.com"
    test_name = "Test Retry"
    
    print(f"\n🧪 [USER SERVICE] Тестирование retry механизма...")
    print(f"🧪 [USER SERVICE] Отправляю уведомление для {test_email}")
    
    # Синхронно вызываем функцию (чтобы видеть все логи сразу)
    result = await send_notification(test_email, test_name)
    
    return {
        "message": "Тест retry завершен",
        "email": test_email,
        "success": result,
        "retry_demonstrated": not result  # Если retry сработал, success=False
    }

@app.get("/users/")
async def get_users(db: Session = Depends(database.get_db)):
    users = db.query(models.User).all()
    return users

@app.get("/health")
async def health_check():
    return {"status": "User Service is healthy"}