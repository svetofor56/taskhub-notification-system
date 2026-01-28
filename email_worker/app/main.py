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
    """Имитация отправки письма с возможностью искусственной ошибки"""
    print(f"📧 [EMAIL WORKER] Начинаю обработку письма для {email}")
    
    # Искусственная ошибка для демонстрации retry (если в email есть "fail")
    if "fail" in email.lower():
        raise Exception(f"Искусственная ошибка для демонстрации retry: email содержит 'fail'")
    
    time.sleep(2)  # Имитация работы
    print(f"✅ [EMAIL WORKER] Письмо 'отправлено' на {email}")
    print(f"   📝 Текст: {message}")
    return True

def callback(ch, method, properties, body):
    """Обработка сообщения с механизмом повторных попыток"""
    max_retries = 3
    processed = False
    
    for attempt in range(1, max_retries + 1):
        try:
            print(f"📨 [ПОПЫТКА {attempt}/{max_retries}] Получено сообщение из очереди")
            print(f"   🏷️ Delivery tag: {method.delivery_tag}")
            print(f"   🔤 Размер сообщения: {len(body)} байт")
            
            # Парсинг JSON
            event = json.loads(body.decode('utf-8'))
            email = event.get('email', 'NO_EMAIL')
            message_text = event.get('message', 'NO_MESSAGE')
            
            print(f"   📧 Email: {email}")
            print(f"   💬 Текст: {message_text}")
            
            # Обработка письма (может вызвать исключение для демонстрации retry)
            success = process_email(email, message_text)
            
            if success:
                # Подтверждаем успешную обработку
                ch.basic_ack(delivery_tag=method.delivery_tag)
                print(f"✅ [EMAIL WORKER] Сообщение успешно обработано (попытка {attempt})")
                print(f"✅ [EMAIL WORKER] Сообщение подтверждено (ACK)")
                processed = True
                break
                
        except json.JSONDecodeError as e:
            print(f"❌ [EMAIL WORKER] ОШИБКА: Невалидный JSON")
            print(f"   🔧 Ошибка: {e}")
            # Не будем повторять попытки для невалидного JSON
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            print(f"❌ [EMAIL WORKER] Сообщение отклонено (NACK) - невалидный JSON")
            break
            
        except KeyError as e:
            print(f"❌ [EMAIL WORKER] ОШИБКА: Отсутствует ключ в JSON")
            print(f"   🔑 Отсутствующий ключ: {e}")
            # Не будем повторять попытки для сообщений с неверной структурой
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            print(f"❌ [EMAIL WORKER] Сообщение отклонено (NACK) - неверная структура JSON")
            break
            
        except Exception as e:
            print(f"❌ [EMAIL WORKER] Ошибка при попытке {attempt}: {e}")
            
            if attempt == max_retries:
                # Достигли лимита попыток
                print(f"🚫 Достигнут лимит {max_retries} попыток. Сообщение отклонено (NACK)")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                print(f"⚠️  Сообщение для {event.get('email', 'unknown')} не удалось обработать")
            else:
                # Экспоненциальная задержка перед следующей попыткой
                delay = 2 ** attempt  # 2, 4, 8 секунд
                print(f"⏱️  Жду {delay} сек. перед повторной попыткой...")
                time.sleep(delay)
    
    if not processed:
        print("⚠️  Сообщение не удалось обработать после всех попыток")
    
    print("-" * 40)

def main():
    print("🔄 [EMAIL WORKER] Подготовка к подключению RabbitMQ...")
    
    # Ждем 10 секунд перед подключением (RabbitMQ может запускаться долго)
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
            
            # Объявляем очередь (должна совпадать с notification_service)
            channel.queue_declare(
                queue='email_queue',
                durable=True,  # Очередь сохраняется при перезагрузке
                arguments={
                    'x-queue-type': 'classic'  # Явно указываем тип очереди
                }
            )
            
            print("   ✅ Очередь 'email_queue' объявлена")
            print("   ⚙️ Настраиваю качество обслуживания (QoS)...")
            
            channel.basic_qos(prefetch_count=1)
            
            print("   👂 Подписываюсь на очередь...")
            channel.basic_consume(
                queue='email_queue',
                on_message_callback=callback,
                auto_ack=False  # Важно! Сами подтверждаем обработку
            )
            
            print("=" * 60)
            print("✅ [EMAIL WORKER] ВСЕ СИСТЕМЫ РАБОТАЮТ")
            print("   Ожидаю сообщения из очереди...")
            print("   Для остановки нажмите CTRL+C")
            print("=" * 60)
            
            # Начинаем слушать очередь
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