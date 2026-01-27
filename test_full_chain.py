import requests 
import time 
import random 
 
print("1. Проверяем health всех сервисов...") 
 
# User Service 
try: 
    resp = requests.get("http://localhost:8000/health") 
    print(f"   User Service: {resp.status_code} - {resp.json()}") 
except Exception as e: 
    print(f"   User Service ERROR: {e}") 
 
# Notification Service 
try: 
    resp = requests.get("http://localhost:8001/health") 
    print(f"   Notification Service: {resp.status_code} - {resp.json()}") 
except Exception as e: 
    print(f"   Notification Service ERROR: {e}") 
 
print("\n2. Отправляем тестовый запрос...") 
try: 
    resp = requests.post( 
        "http://localhost:8000/users/", 
        json={"email": f"test{random.randint(1, 1000000)}@example.com", "name": "Test User"} 
    ) 
    print(f"   Status: {resp.status_code}") 
    print(f"   Response: {resp.json()}") 
except Exception as e: 
    print(f"   ERROR: {e}") 
 
print("\n3. Ждем 3 секунды и проверяем очередь...") 
time.sleep(3) 
 
print("\n4. Проверяем, что пользователь создался...") 
try: 
    resp = requests.get("http://localhost:8000/users/") 
    print(f"   Users: {resp.json()}") 
except Exception as e: 
    print(f"   ERROR: {e}")