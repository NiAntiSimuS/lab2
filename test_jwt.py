import requests
import json
import time
import jwt  

BASE_URL = "http://localhost:5000"

def print_section(title):
    """Печатает заголовок раздела"""
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)

def test_jwt_login():
    """Тест получения JWT токенов"""
    print_section("ТЕСТ: ПОЛУЧЕНИЕ JWT ТОКЕНОВ")
    
    # Тестовые данные пользователя
    login_data = {
        "email": "test@example.com",
        "password": "testpassword"
    }
    
    print(f"Пытаемся войти с данными:")
    print(f"  Email: {login_data['email']}")
    print(f"  Пароль: {login_data['password']}")
    
    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    print(f"\nURL: POST {BASE_URL}/api/auth/login")
    print(f"Статус ответа: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nУспешная аутентификация!")
        print(f"  Сообщение: {data.get('message')}")
        print(f"  Access токен: {data.get('access_token')[:50]}...")
        print(f"  Refresh токен: {data.get('refresh_token')[:50]}...")
        print(f"  Пользователь: {data.get('user')['name']} ({data.get('user')['email']})")
        
        # Декодируем токен для проверки содержимого
        try:
            access_token = data.get('access_token')
            decoded = jwt.decode(access_token, options={"verify_signature": False})
            print(f"\nСодержимое access токена:")
            print(f"  User ID: {decoded.get('user_id')}")
            print(f"  Тип: {decoded.get('type')}")
            print(f"  Выдан (iat): {decoded.get('iat')}")
            print(f"  Истекает (exp): {decoded.get('exp')}")
        except Exception as e:
            print(f"Ошибка декодирования токена: {e}")
        
        return data.get('access_token'), data.get('refresh_token'), data.get('user')
    else:
        print(f"\nОшибка при аутентификации: {response.status_code}")
        print(f"Ответ: {response.text}")
        return None, None, None

def test_protected_endpoint(access_token):
    """Тест доступа к защищенному эндпоинту"""
    print_section("ТЕСТ: ДОСТУП К ЗАЩИЩЕННОМУ ЭНДПОИНТУ")
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    print(f"Заголовок Authorization: Bearer {access_token[:30]}...")
    
    response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
    print(f"\nURL: GET {BASE_URL}/api/auth/me")
    print(f"Статус ответа: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nУспешный доступ к защищенному эндпоинту!")
        print(f"  Пользователь: {data.get('name')}")
        print(f"  Email: {data.get('email')}")
        print(f"  ID: {data.get('id')}")
        return True
    else:
        print(f"\nОшибка доступа: {response.status_code}")
        print(f"Ответ: {response.text}")
        return False

def test_token_refresh(refresh_token):
    """Тест обновления access токена"""
    print_section("ТЕСТ: ОБНОВЛЕНИЕ ACCESS ТОКЕНА")
    
    refresh_data = {
        "refresh_token": refresh_token
    }
    
    print(f"Используем refresh токен: {refresh_token[:50]}...")
    
    response = requests.post(f"{BASE_URL}/api/auth/refresh", json=refresh_data)
    print(f"\nURL: POST {BASE_URL}/api/auth/refresh")
    print(f"Статус ответа: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nТокен успешно обновлен!")
        print(f"  Сообщение: {data.get('message')}")
        print(f"  Новый access токен: {data.get('access_token')[:50]}...")
        return data.get('access_token')
    else:
        print(f"\nОшибка при обновлении токена: {response.status_code}")
        print(f"Ответ: {response.text}")
        return None

def test_jwt_logout(access_token, refresh_token):
    """Тест выхода из системы"""
    print_section("ТЕСТ: ВЫХОД ИЗ СИСТЕМЫ")
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    logout_data = {
        "refresh_token": refresh_token
    }
    
    print(f"Отзыв refresh токена: {refresh_token[:50]}...")
    
    response = requests.post(f"{BASE_URL}/api/auth/logout", headers=headers, json=logout_data)
    print(f"\nURL: POST {BASE_URL}/api/auth/logout")
    print(f"Статус ответа: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nУспешный выход из системы!")
        print(f"  Сообщение: {data.get('message')}")
        
        # Пытаемся использовать отозванный refresh токен
        print(f"\nПроверка: пытаемся использовать отозванный refresh токен...")
        refresh_data = {"refresh_token": refresh_token}
        response = requests.post(f"{BASE_URL}/api/auth/refresh", json=refresh_data)
        
        if response.status_code != 200:
            print(f"  Отозванный токен больше не работает - УСПЕХ!")
        else:
            print(f"  Отозванный токен все еще работает - ПРОВАЛ!")
            
        return True
    else:
        print(f"\nОшибка при выходе: {response.status_code}")
        print(f"Ответ: {response.text}")
        return False

def test_create_article_with_jwt(access_token):
    """Тест создания статьи с JWT аутентификацией"""
    print_section("ТЕСТ: СОЗДАНИЕ СТАТЬИ С JWT")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    article_data = {
        "title": "Статья созданная через JWT API",
        "content": "Это содержимое статьи, созданной с использованием JWT аутентификации. " +
                  "Статья должна быть успешно создана, так как у нас есть валидный токен.",
        "category": "technology"
    }
    
    print(f"Создаем статью с JWT аутентификацией:")
    print(f"  Заголовок: {article_data['title']}")
    print(f"  Категория: {article_data['category']}")
    
    response = requests.post(f"{BASE_URL}/api/articles", headers=headers, json=article_data)
    print(f"\nURL: POST {BASE_URL}/api/articles")
    print(f"Статус ответа: {response.status_code}")
    
    if response.status_code == 201:
        article = response.json()
        print(f"\nСтатья успешно создана с JWT!")
        print(f"  ID статьи: {article.get('id')}")
        print(f"  Заголовок: {article.get('title')}")
        print(f"  Автор: {article.get('author_name')}")
        return article.get('id')
    else:
        print(f"\nОшибка при создании статьи: {response.status_code}")
        print(f"Ответ: {response.text}")
        return None

def test_access_without_token():
    """Тест доступа без токена"""
    print_section("ТЕСТ: ДОСТУП БЕЗ ТОКЕНА")
    
    print("1. Попытка доступа к защищенному эндпоинту без токена:")
    response = requests.get(f"{BASE_URL}/api/auth/me")
    print(f"   URL: GET {BASE_URL}/api/auth/me")
    print(f"   Статус: {response.status_code}")
    
    if response.status_code == 401:
        print(f"   Доступ запрещен - УСПЕХ!")
    else:
        print(f"   Неожиданный статус - ПРОВАЛ!")
    
    print("\n2. Попытка создания статьи без токена:")
    article_data = {
        "title": "Статья без токена",
        "content": "Эта статья не должна быть создана",
        "category": "general"
    }
    
    response = requests.post(f"{BASE_URL}/api/articles", json=article_data)
    print(f"   URL: POST {BASE_URL}/api/articles")
    print(f"   Статус: {response.status_code}")
    
    if response.status_code == 401:
        print(f"   Доступ запрещен - УСПЕХ!")
    else:
        print(f"   Неожиданный статус - ПРОВАЛ!")

def test_invalid_token():
    """Тест с невалидным токеном"""
    print_section("ТЕСТ: НЕВАЛИДНЫЙ ТОКЕН")
    
    invalid_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    
    headers = {
        "Authorization": f"Bearer {invalid_token}"
    }
    
    print(f"Используем заведомо невалидный токен")
    
    response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
    print(f"\nURL: GET {BASE_URL}/api/auth/me")
    print(f"Статус ответа: {response.status_code}")
    
    if response.status_code == 401:
        print(f"Доступ с невалидным токеном запрещен - УСПЕХ!")
    else:
        print(f"Неожиданный статус - ПРОВАЛ!")

def test_complete_jwt_workflow():
    """Полный тест JWT workflow"""
    print_section("ПОЛНЫЙ ТЕСТ JWT WORKFLOW")
    
    print("1. Регистрация нового пользователя (если нужно)")
    print("2. Получение JWT токенов")
    print("3. Доступ к защищенным ресурсам")
    print("4. Обновление токена")
    print("5. Выход из системы")
    print("6. Проверка, что отозванный токен не работает")

def test_jwt_with_json_sync():
    """Тест синхронизации JSON файлов после операций с JWT"""
    print_section("ТЕСТ: СИНХРОНИЗАЦИЯ JSON ФАЙЛОВ С JWT")
    
    print("1. Создаем статью через JWT API")
    print("2. Проверяем, что статья появилась в JSON файле")
    print("3. Проверяем, что статья доступна через обычный API")
    
    # Получаем токен
    access_token, refresh_token, user = test_jwt_login()
    
    if access_token:
        # Создаем статью
        headers = {"Authorization": f"Bearer {access_token}"}
        article_data = {
            "title": "Статья для проверки JSON синхронизации",
            "content": "Эта статья должна появиться в articles.json файле",
            "category": "science"
        }
        
        response = requests.post(f"{BASE_URL}/api/articles", headers=headers, json=article_data)
        
        if response.status_code == 201:
            article_id = response.json().get('id')
            print(f"\nСтатья создана с ID: {article_id}")
            
            # Даем время на синхронизацию
            time.sleep(1)
            
            # Проверяем через обычный API
            response = requests.get(f"{BASE_URL}/api/articles/{article_id}")
            if response.status_code == 200:
                print("Статья доступна через обычный API - УСПЕХ!")
            else:
                print("Статья не доступна через обычный API - ПРОВАЛ!")
            
            # Проверяем через JSON API
            response = requests.get(f"{BASE_URL}/api/json/articles")
            if response.status_code == 200:
                articles = response.json()
                found = any(a.get('id') == article_id for a in articles)
                if found:
                    print("Статья найдена в JSON файле - УСПЕХ!")
                else:
                    print("Статья не найдена в JSON файле - ПРОВАЛ!")

def main():
    """Основная функция тестирования JWT"""
    print("\n" + "=" * 70)
    print("НАЧАЛО ТЕСТИРОВАНИЯ JWT АУТЕНТИФИКАЦИИ")
    print("=" * 70)
    
    # Проверяем доступность сервера
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code != 200:
            print("Сервер не отвечает. Запустите Flask приложение сначала.")
            return
    except:
        print("Не удалось подключиться к серверу. Убедитесь, что приложение запущено.")
        return
    
    # Регистрируем тестового пользователя (если нужно)
    print("\nПодготовка: проверка тестового пользователя...")
    
    # Запускаем тесты
    test_access_without_token()
    test_invalid_token()
    
    # Получаем токены
    access_token, refresh_token, user = test_jwt_login()
    
    if access_token:
        # Тестируем защищенные эндпоинты
        test_protected_endpoint(access_token)
        
        # Создаем статью с JWT
        article_id = test_create_article_with_jwt(access_token)
        
        # Обновляем токен
        new_access_token = test_token_refresh(refresh_token)
        
        if new_access_token:
            # Тестируем с новым токеном
            test_protected_endpoint(new_access_token)
        
        # Тестируем JSON синхронизацию
        test_jwt_with_json_sync()
        
        # Выходим из системы
        test_jwt_logout(access_token, refresh_token)
    
    test_complete_jwt_workflow()
    
    print("\n" + "=" * 70)
    print("ТЕСТИРОВАНИЕ JWT ЗАВЕРШЕНО")
    print("=" * 70)
    
    print("\n" + "=" * 70)
    print("КРАТКОЕ РУКОВОДСТВО ПО ИСПОЛЬЗОВАНИЮ JWT")
    print("=" * 70)
    print("\n1. Получение токенов:")
    print("   POST /api/auth/login")
    print("   Body: {\"email\": \"user@example.com\", \"password\": \"password\"}")
    
    print("\n2. Использование access токена:")
    print("   Добавьте заголовок: Authorization: Bearer <access_token>")
    
    print("\n3. Обновление токена:")
    print("   POST /api/auth/refresh")
    print("   Body: {\"refresh_token\": \"<refresh_token>\"}")
    
    print("\n4. Выход из системы:")
    print("   POST /api/auth/logout")
    print("   Headers: Authorization: Bearer <access_token>")
    print("   Body: {\"refresh_token\": \"<refresh_token>\"}")
    
    print("\n5. Пример использования в JavaScript:")
    print("   fetch('/api/articles', {")
    print("     method: 'POST',")
    print("     headers: {")
    print("       'Authorization': 'Bearer ' + accessToken,")
    print("       'Content-Type': 'application/json'")
    print("     },")
    print("     body: JSON.stringify({")
    print("       title: 'Новая статья',")
    print("       content: 'Текст статьи',")
    print("       category: 'technology'")
    print("     })")
    print("   })")

if __name__ == "__main__":
    main()
