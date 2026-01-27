graph TB
    Client[Клиент] -->|HTTP| UserService[User Service<br/>:8000]
    UserService -->|SQL| PostgreSQL[(PostgreSQL)]
    UserService -->|HTTP| Notification[Notification Service<br/>:8001]
    Notification -->|AMQP| RabbitMQ[(RabbitMQ<br/>:5672, :15672)]
    RabbitMQ -->|Сообщения| EmailWorker[Email Worker]
    EmailWorker -->|Логи| Console[Консоль]
