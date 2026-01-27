# TaskHub - Микросервисная система уведомлений

## Описание проекта
Упрощенная версия системы TaskHub, состоящая из трех микросервисов:
1. **User Service** - REST API для управления пользователями
2. **Notification Service** - Сервис уведомлений через RabbitMQ
3. **Email Worker** - Фоновый процесс для "отправки" email

## Архитектура

```mermaid
graph TD
    A[Клиент] -->|POST /users/| B[User Service]
    B -->|Сохраняет в| C[(PostgreSQL)]
    B -->|Асинхронный HTTP вызов| D[Notification Service]
    D -->|Публикует событие| E[(RabbitMQ)]
    F[Email Worker] -->|Подписан на очередь| E
    F -->|Имитация отправки| G[Лог/Консоль]

    Технологический стек
Backend: Python, FastAPI

Message Broker: RabbitMQ

Database: PostgreSQL

Containerization: Docker, Docker Compose

API Documentation: Swagger/OpenAPI

Структура проекта
taskhub-notification-system/
├── user_service/          # Сервис пользователей
├── notification_service/  # Сервис уведомлений
├── email_worker/          # Фоновый обработчик
├── docker-compose.yml     # Конфигурация Docker
└── README.md              # Документация
Запуск системы
Требования
-Docker Desktop
-Git

Установка и запуск
bash
# 1. Клонировать репозиторий
git clone <ваш-репозиторий>

# 2. Перейти в папку проекта
cd taskhub-notification-system

# 3. Запустить все сервисы
docker-compose up --build

# 4. Система будет доступна на портах:
#    - User Service: http://localhost:8000
#    - Notification Service: http://localhost:8001
#    - RabbitMQ UI: http://localhost:15672 (guest/guest)

Примеры использования
1. Создание пользователя
bash
curl -X POST http://localhost:8000/users/ \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "name": "Test User"}'
2. Получение списка пользователей
bash
curl http://localhost:8000/users/
3. Проверка здоровья сервисов
bash
curl http://localhost:8000/health
curl http://localhost:8001/health

4. Прямая отправка уведомления
bash
curl -X POST http://localhost:8001/notify \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "message": "Test Message"}'

  API Документация
User Service Swagger UI: http://localhost:8000/docs

Notification Service Swagger UI: http://localhost:8001/docs

Наблюдение за системой
Логи сервисов
bash
# Просмотр логов всех сервисов
docker-compose logs -f

# Логи конкретного сервиса
docker-compose logs -f user_service
docker-compose logs -f email_worker
Мониторинг RabbitMQ
RabbitMQ Management UI: http://localhost:15672

Логин: guest, Пароль: guest

Проверьте очередь email_queue во вкладке Queues

Тестирование
Для запуска тестового сценария:
powershell
python test_full_chain.py

bash
# Остановка с удалением контейнеров
docker-compose down

# Остановка с удалением контейнеров и томов
docker-compose down -v

Разработка
Для разработки и отладки:

bash
# Пересобрать конкретный сервис
docker-compose build user_service

# Запустить только определенные сервисы
docker-compose up -d rabbitmq notification_service

# Зайти внутрь контейнера
docker-compose exec user_service sh

## Postman Collection

Для тестирования API доступна Postman коллекция:

1. Скачайте файл [TaskHub_Postman_Collection.json](TaskHub_Postman_Collection.json)
2. Импортируйте в Postman: File → Import → Выберите файл
3. Все запросы готовы к использованию

## Архитектура системы

```mermaid
graph TB
    Client[Клиент] -->|HTTP REST API| UserService[User Service :8000]
    UserService -->|SQL| PostgreSQL[(PostgreSQL<br/>База данных)]
    UserService -->|HTTP POST| NotificationService[Notification Service :8001]
    NotificationService -->|AMQP| RabbitMQ[(RabbitMQ<br/>Очередь сообщений)]
    RabbitMQ -->|Сообщения| EmailWorker[Email Worker]
    EmailWorker -->|Логирование| Console[Консоль Docker]
    
    style Client fill:#e1f5fe,stroke:#01579b
    style UserService fill:#f3e5f5,stroke:#4a148c
    style PostgreSQL fill:#e8f5e8,stroke:#1b5e20
    style NotificationService fill:#f3e5f5,stroke:#4a148c
    style RabbitMQ fill:#fff3e0,stroke:#e65100
    style EmailWorker fill:#fce4ec,stroke:#880e4f
    style Console fill:#f5f5f5,stroke:#616161
```

Автор
[Передеренко Никита Вячеславович; Магистратура; Прикладная информатика 2 курс/НВРС24-М-ЦР02]

Лицензия
Учебный проект