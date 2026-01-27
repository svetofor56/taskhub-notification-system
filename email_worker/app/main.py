#!/usr/bin/env python
import pika
import json
import time
import sys
import traceback

# Принудительно сбрасываем буфер вывода после каждого print
import functools
print = functools.partial(print, flush=True)

print("=" * 60)
print("🚀 EMAIL WORKER ЗАПУЩЕН")
print("=" * 60)

def process_email(email: str, message: str):
    print(f"📧 [EMAIL WORKER] Начинаю обработку письма для {email}")
    time.sleep(2)  # Имитация работы
    print(f"✅ [EMAIL WORKER] Письмо 'отправлено' на {email}")
    print(f"   📝 Текст: {message}")
    return True

def callback(ch, method, properties, body):
    print(f"📨 [EMAIL WORKER] Получено новое сообщение из очереди")
    print(f"   🏷️ Delivery tag: {method.delivery_tag}")
    print(f"   🔤 Размер сообщения: {len(body)} байт")
    
    try:
        
        print(f"   🛠️ Парсинг JSON...")
        event = json.loads(body.decode('utf-8'))
        print(f"   ✅ JSON распарсен успешно")
        
        # Извлекаем данные
        email = event.get('email', 'NO_EMAIL')
        message_text = event.get('message', 'NO_MESSAGE')
        
        print(f"   📧 Email из сообщения: {email}")
        print(f"   💬 Текст сообщения: {message_text}")
        
        # Обрабатываем письмо
        success = process_email(email, message_text)
        
        if success:
            
            ch.basic_ack(delivery_tag=method.delivery_tag)
            print(f"✅ [EMAIL WORKER] Сообщение подтверждено (ACK)")
        else:
            
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            print(f"❌ [EMAIL WORKER] Сообщение отклонено (NACK)")
            
    except json.JSONDecodeError as e:
        print(f"❌ [EMAIL WORKER] ОШИБКА: Невалидный JSON")
        print(f"   📄 Сырое сообщение: {body}")
        print(f"   🔧 Ошибка: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        
    except KeyError as e:
        print(f"❌ [EMAIL WORKER] ОШИБКА: Отсутствует ключ в JSON")
        print(f"   🔑 Отсутствующий ключ: {e}")
        print(f"   📊 Данные: {event}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        
    except Exception as e:
        print(f"❌ [EMAIL WORKER] НЕОЖИДАННАЯ ОШИБКА:")
        print(f"   ⚠️ Тип: {type(e).__name__}")
        print(f"   📝 Сообщение: {str(e)}")
        print("   🔍 Stack trace:")
        traceback.print_exc()
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    
    print("-" * 40)

def main():
    print("🔄 [EMAIL WORKER] Подготовка к подключению RabbitMQ...")
    

    time.sleep(10)
    
    retry_count = 0
    max_retries = 10
    
    while retry_count < max_retries:
        try:
            print(f"🔄 [EMAIL WORKER] Попытка подключения {retry_count + 1}/{max_retries}...")
            
            connection_params = pika.ConnectionParameters(
                host='rabbitmq',
                port=5672,
                credentials=pika.PlainCredentials('guest', 'guest'),
                heartbeat=600,
                connection_attempts=3,
                retry_delay=5,
                socket_timeout=5
            )
            
            print("   🔗 Создаю соединение с RabbitMQ...")
            connection = pika.BlockingConnection(connection_params)
            channel = connection.channel()
            
            print("   ✅ Подключение к RabbitMQ успешно!")
            print("   📋 Объявляю очередь 'email_queue'...")
            
            # Объявляем очередь 
            channel.queue_declare(
                queue='email_queue',
                durable=True,  # Очередь сохраняется при перезагрузке
                arguments={
                    'x-queue-type': 'classic'  
                }
            )
            
            print("   ✅ Очередь 'email_queue' объявлена")
            print("   ⚙️ Настраиваю качество обслуживания (QoS)...")
            
            channel.basic_qos(prefetch_count=1)
            
            print("   👂 Подписываюсь на очередь...")
            channel.basic_consume(
                queue='email_queue',
                on_message_callback=callback,
                auto_ack=False  
            )
            
            print("=" * 60)
            print("✅ [EMAIL WORKER] ВСЕ СИСТЕМЫ РАБОТАЮТ")
            print("   Ожидаю сообщения из очереди...")
            print("   Для остановки нажмите CTRL+C")
            print("=" * 60)
            
          
            channel.start_consuming()
            
        except pika.exceptions.AMQPConnectionError as e:
            retry_count += 1
            print(f"❌ [EMAIL WORKER] Не удалось подключиться к RabbitMQ")
            print(f"   ⚠️ Ошибка: {e}")
            print(f"   🔄 Повторная попытка через 10 секунд...")
            time.sleep(10)
            
        except KeyboardInterrupt:
            print("\n\n🛑 [EMAIL WORKER] Остановка по запросу пользователя...")
            if 'connection' in locals() and connection.is_open:
                connection.close()
            print("✅ [EMAIL WORKER] Корректно завершил работу")
            sys.exit(0)
            
        except Exception as e:
            print(f"❌ [EMAIL WORKER] Критическая ошибка: {e}")
            traceback.print_exc()
            retry_count += 1
            time.sleep(10)
    
    print(f"❌ [EMAIL WORKER] Достигнут лимит попыток подключения ({max_retries})")
    print("   Завершение работы...")
    sys.exit(1)

if __name__ == '__main__':
    main()