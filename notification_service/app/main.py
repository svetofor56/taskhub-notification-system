import pika
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Notification Service")

# Модель для входящего запроса
class NotificationRequest(BaseModel):
    email: str
    message: str

# Функция для подключения к RabbitMQ и публикации сообщения
def publish_to_rabbitmq(email: str, message: str):
    try:
        # Параметры подключения. Имя хоста берем из docker-compose
        connection_params = pika.ConnectionParameters(
            host='rabbitmq',
            port=5672,
            credentials=pika.PlainCredentials('guest', 'guest')
        )
        connection = pika.BlockingConnection(connection_params)
        channel = connection.channel()

        # Объявляем очередь (если не существует)
        channel.queue_declare(queue='email_queue', durable=True)

        # Формируем сообщение
        notification_event = {
            "email": email,
            "message": message
        }
        body = json.dumps(notification_event)

        # Публикуем сообщение в очередь
        channel.basic_publish(
            exchange='',
            routing_key='email_queue',
            body=body,
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE  # Сохраняем сообщение при перезагрузке
            )
        )
        print(f" [x] Сообщение отправлено в очередь для {email}")
        connection.close()
    except Exception as e:
        print(f"Ошибка при работе с RabbitMQ: {e}")
        raise

@app.post("/notify")
async def notify(request: NotificationRequest):
    try:
        # Публикуем событие в RabbitMQ
        publish_to_rabbitmq(request.email, request.message)
        return {"status": "Уведомление принято в обработку"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при обработке уведомления: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "Notification Service is healthy"}

@app.post("/test-notify")
async def test_notify():
    """Тестовый эндпоинт для проверки email_worker"""
    test_data = {
        "email": "test@notification.com",
        "message": "Тестовое сообщение из Notification Service"
    }
    
    try:
        publish_to_rabbitmq(test_data["email"], test_data["message"])
        return {
            "status": "success",
            "message": "Тестовое сообщение отправлено в очередь",
            "data": test_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")