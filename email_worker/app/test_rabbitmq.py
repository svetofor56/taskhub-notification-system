import pika
import json

# Тест подключения к RabbitMQ
connection_params = pika.ConnectionParameters(
    host='rabbitmq',
    port=5672,
    credentials=pika.PlainCredentials('guest', 'guest')
)

try:
    connection = pika.BlockingConnection(connection_params)
    channel = connection.channel()
    
    # Проверяем очередь
    result = channel.queue_declare(queue='email_queue', passive=True)
    print(f"Очередь существует. Сообщений в очереди: {result.method.message_count}")
    
    # Пробуем получить одно сообщение
    method, properties, body = channel.basic_get(queue='email_queue', auto_ack=True)
    
    if body:
        print(f"Получено сообщение: {body}")
        event = json.loads(body)
        print(f"Email: {event['email']}")
        print(f"Message: {event['message']}")
    else:
        print("Очередь пуста")
        
    connection.close()
    
except Exception as e:
    print(f"Ошибка: {e}")