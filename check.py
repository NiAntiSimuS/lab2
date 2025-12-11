import requests
import time
from bs4 import BeautifulSoup

BASE_URL = "http://localhost:5000"

def create_authenticated_session(email="test@example.com", password="testpassword"):
    """Создает аутентифицированную сессию"""
    session = requests.Session()
    
    login_data = {
        "email": email,
        "password": password
    }
    
    response = session.post(f"{BASE_URL}/login", data=login_data)
    if response.status_code == 200:
        print(f"Успешный логин: {response.status_code}")
        return session
    
    register_data = {
        "name": "Test User",
        "email": email,
        "password": password
    }
    
    response = session.post(f"{BASE_URL}/register", data=register_data)
    print(f"Регистрация: {response.status_code}")
    
    response = session.post(f"{BASE_URL}/login", data=login_data)
    print(f"Логин после регистрации: {response.status_code}")
    
    return session

def print_section(title):
    """Печатает заголовок раздела"""
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)

def test_get_all_articles(session=None):
    """Тест получения всех статей"""
    print_section("ТЕСТ: ПОЛУЧЕНИЕ ВСЕХ СТАТЕЙ ЧЕРЕЗ API")
    
    if session:
        response = session.get(f"{BASE_URL}/api/articles")
    else:
        response = requests.get(f"{BASE_URL}/api/articles")
    
    print(f"URL: GET {BASE_URL}/api/articles")
    print(f"Статус ответа: {response.status_code}")
    
    if response.status_code == 200:
        articles = response.json()
        print(f"Найдено статей: {len(articles)}")
        
        if articles:
            for i, article in enumerate(articles, 1):
                print(f"\nСтатья #{i}:")
                print(f"  ID: {article.get('id')}")
                print(f"  Заголовок: {article.get('title')}")
                print(f"  Категория: {article.get('category')}")
                print(f"  Автор: {article.get('author_name', 'Неизвестен')}")
                
                created_date = article.get('created_date', '')
                if created_date and 'T' in created_date:
                    date_part = created_date.split('T')[0]
                    print(f"  Дата создания: {date_part}")
                
                content = article.get('content') or article.get('text', '')
                if content:
                    preview = content[:150] + "..." if len(content) > 150 else content
                    print(f"  Содержание: {preview}")
                
                comments_count = article.get('comments_count', 0)
                print(f"  Комментариев: {comments_count}")
        else:
            print("Список статей пуст")
    else:
        print(f"Ошибка: {response.text}")

def test_get_article_by_id(session=None):
    """Тест получения конкретной статьи по ID"""
    print_section("ТЕСТ: ПОЛУЧЕНИЕ СТАТЬИ ПО ID")
    
    if session:
        all_articles_response = session.get(f"{BASE_URL}/api/articles")
    else:
        all_articles_response = requests.get(f"{BASE_URL}/api/articles")
    
    if all_articles_response.status_code == 200:
        articles = all_articles_response.json()
        if articles:
            article_id = articles[0]['id']
            
            print(f"Тестируем статью с ID: {article_id}")
            if session:
                response = session.get(f"{BASE_URL}/api/articles/{article_id}")
            else:
                response = requests.get(f"{BASE_URL}/api/articles/{article_id}")
            
            print(f"URL: GET {BASE_URL}/api/articles/{article_id}")
            print(f"Статус ответа: {response.status_code}")
            
            if response.status_code == 200:
                article = response.json()
                print(f"\nПолная информация о статье:")
                print(f"  ID: {article.get('id')}")
                print(f"  Заголовок: {article.get('title')}")
                print(f"  Категория: {article.get('category')}")
                print(f"  Автор: {article.get('author_name', 'Неизвестен')}")
                print(f"  Дата: {article.get('created_date')}")
                print(f"  Комментариев: {article.get('comments_count', 0)}")
                
                content = article.get('content') or article.get('text', '')
                if content:
                    if len(content) > 200:
                        print(f"  Содержание (первые 200 символов): {content[:200]}...")
                    else:
                        print(f"  Содержание: {content}")
            else:
                print(f"Ошибка: {response.text}")
        else:
            print("В системе нет статей для тестирования")
    else:
        print(f"Не удалось получить список статей: {all_articles_response.status_code}")

def test_create_article(session):
    """Тест создания новой статьи через API (требует аутентификации)"""
    print_section("ТЕСТ: СОЗДАНИЕ НОВОЙ СТАТЬИ ЧЕРЕЗ API")
    
    article_data = {
        "title": "Тестовая статья созданная через API",
        "content": "Это содержимое тестовой статьи, созданной через API запрос. " +
                  "Статья должна появиться в системе и быть доступна для чтения.",
        "category": "technology"
    }
    
    print(f"Создаем статью с данными:")
    print(f"  Заголовок: {article_data['title']}")
    print(f"  Категория: {article_data['category']}")
    print(f"  Содержание (первые 100 символов): {article_data['content'][:100]}...")
    
    response = session.post(f"{BASE_URL}/api/articles", json=article_data)
    print(f"\nURL: POST {BASE_URL}/api/articles")
    print(f"Статус ответа: {response.status_code}")
    
    if response.status_code == 201:
        new_article = response.json()
        print(f"\nСтатья успешно создана!")
        print(f"  ID новой статьи: {new_article.get('id')}")
        print(f"  Заголовок: {new_article.get('title')}")
        print(f"  Категория: {new_article.get('category')}")
        print(f"  Автор: {new_article.get('author_name', 'Неизвестен')}")
        
        print(f"\nПроверка: ищем созданную статью в общем списке...")
        time.sleep(1)  
        
        list_response = session.get(f"{BASE_URL}/api/articles")
        if list_response.status_code == 200:
            all_articles = list_response.json()
            new_article_found = any(
                article.get('title') == article_data['title'] 
                for article in all_articles
            )
            if new_article_found:
                print("  Статья найдена в общем списке - УСПЕХ!")
            else:
                print("  Статья не найдена в общем списке - ПРОВАЛ!")
        
        return new_article.get('id')  #
    else:
        print(f"\nОшибка при создании статьи: {response.text}")
        return None

def test_update_article(session, article_id):
    """Тест обновления существующей статьи (требует аутентификации)"""
    print_section("ТЕСТ: ОБНОВЛЕНИЕ СУЩЕСТВУЮЩЕЙ СТАТЬИ")
    
    if not article_id:
        print("Нет ID статьи для обновления")
        return
    
    update_data = {
        "title": "Обновленный заголовок тестовой статьи",
        "content": "Это обновленное содержание статьи. " +
                  "Теперь статья содержит новую информацию после редактирования через API.",
        "category": "science"
    }
    
    print(f"Обновляем статью с ID: {article_id}")
    print(f"Новые данные:")
    print(f"  Заголовок: {update_data['title']}")
    print(f"  Категория: {update_data['category']}")
    
    response = session.put(f"{BASE_URL}/api/articles/{article_id}", json=update_data)
    print(f"\nURL: PUT {BASE_URL}/api/articles/{article_id}")
    print(f"Статус ответа: {response.status_code}")
    
    if response.status_code == 200:
        updated_article = response.json()
        print(f"\nСтатья успешно обновлена!")
        print(f"  ID статьи: {updated_article.get('id')}")
        print(f"  Новый заголовок: {updated_article.get('title')}")
        print(f"  Новая категория: {updated_article.get('category')}")
        
        get_response = session.get(f"{BASE_URL}/api/articles/{article_id}")
        if get_response.status_code == 200:
            final_article = get_response.json()
            if final_article.get('title') == update_data['title']:
                print("  Изменения подтверждены - УСПЕХ!")
            else:
                print("  Изменения не применились - ПРОВАЛ!")
    else:
        print(f"\nОшибка при обновлении статьи: {response.text}")

def test_get_articles_by_category():
    """Тест получения статей по категории"""
    print_section("ТЕСТ: СТАТЬИ ПО КАТЕГОРИИ")
    
    categories = ['technology', 'science', 'culture', 'sports', 'general']
    
    for category in categories:
        print(f"\nКатегория: {category.upper()}")
        response = requests.get(f"{BASE_URL}/api/articles/category/{category}")
        print(f"URL: GET {BASE_URL}/api/articles/category/{category}")
        print(f"Статус: {response.status_code}")
        
        if response.status_code == 200:
            articles = response.json()
            print(f"Найдено статей: {len(articles)}")
            
            for i, article in enumerate(articles[:3], 1):  # Показываем первые 3
                print(f"  {i}. {article.get('title')} (ID: {article.get('id')})")
                
            if len(articles) > 3:
                print(f"  ... и еще {len(articles) - 3} статей")
            elif not articles:
                print(f"  В этой категории пока нет статей")
        else:
            print(f"  Ошибка: {response.text}")

def test_json_endpoints():
    """Тестирование JSON эндпоинтов"""
    print_section("ТЕСТИРОВАНИЕ JSON ЭНДПОИНТОВ")
    
    print("\nСтатьи из JSON файла:")
    response = requests.get(f"{BASE_URL}/api/json/articles")
    print(f"URL: GET {BASE_URL}/api/json/articles")
    print(f"Статус: {response.status_code}")
    
    if response.status_code == 200:
        articles = response.json()
        print(f"Статей в JSON файле: {len(articles)}")
        if articles:
            print("Первые 3 статьи из JSON:")
            for i, article in enumerate(articles[:3], 1):
                print(f"  {i}. {article.get('title')} (ID: {article.get('id')})")
    
    print("\nКомментарии из JSON файла:")
    response = requests.get(f"{BASE_URL}/api/json/comments")
    print(f"URL: GET {BASE_URL}/api/json/comments")
    print(f"Статус: {response.status_code}")
    
    if response.status_code == 200:
        comments = response.json()
        print(f"Комментариев в JSON файле: {len(comments)}")
        if comments:
            print("Первые 3 комментария из JSON:")
            for i, comment in enumerate(comments[:3], 1):
                print(f"  {i}. {comment.get('author_name')}: {comment.get('text')[:50]}...")

def test_debug_endpoints():
    """Тестирование отладочных эндпоинтов"""
    print_section("ТЕСТИРОВАНИЕ ОТЛАДОЧНЫХ ЭНДПОИНТОВ")
    
    debug_endpoints = [
        ("/api/debug/articles", "Статьи из базы данных"),
        ("/api/debug/comments", "Комментарии из базы данных"),
        ("/api/debug/users", "Пользователи из базы данных")
    ]
    
    for endpoint, description in debug_endpoints:
        print(f"\n{description}:")
        response = requests.get(f"{BASE_URL}{endpoint}")
        print(f"URL: GET {BASE_URL}{endpoint}")
        print(f"Статус: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Элементов получено: {len(data)}")
            
            if data and len(data) > 0:
                first_item = data[0]
                print(f"Первый элемент:")
                for key, value in first_item.items():
                    if isinstance(value, str) and len(value) > 100:
                        print(f"  {key}: {value[:100]}...")
                    else:
                        print(f"  {key}: {value}")

def test_comments_api():
    """Тестирование API для комментариев"""
    print_section("ТЕСТИРОВАНИЕ API ДЛЯ КОММЕНТАРИЕВ")
    
    print("\n1. Получение всех комментариев:")
    response = requests.get(f"{BASE_URL}/api/comment")
    print(f"URL: GET {BASE_URL}/api/comment")
    print(f"Статус: {response.status_code}")
    
    if response.status_code == 200:
        comments = response.json()
        print(f"Всего комментариев: {len(comments)}")
        
        if comments:
            print("Последние 3 комментария:")
            for i, comment in enumerate(comments[:3], 1):
                print(f"  {i}. {comment.get('author_name')}: {comment.get('text')[:50]}...")
    
    print("\n2. Создание нового комментария:")
    
    articles_response = requests.get(f"{BASE_URL}/api/articles")
    if articles_response.status_code == 200:
        articles = articles_response.json()
        if articles:
            article_id = articles[0]['id']
            article_title = articles[0]['title']
            
            comment_data = {
                "text": "Это тестовый комментарий, созданный через API",
                "author_name": "Тестовый пользователь",
                "article_id": article_id
            }
            
            print(f"Создаем комментарий для статьи: {article_title} (ID: {article_id})")
            response = requests.post(f"{BASE_URL}/api/comment", json=comment_data)
            print(f"URL: POST {BASE_URL}/api/comment")
            print(f"Статус: {response.status_code}")
            
            if response.status_code == 201:
                new_comment = response.json()
                print(f"Комментарий успешно создан!")
                print(f"  ID комментария: {new_comment.get('id')}")
                print(f"  Автор: {new_comment.get('author_name')}")
                print(f"  Текст: {new_comment.get('text')}")
            else:
                print(f"Ошибка при создании комментария: {response.text}")

def test_web_pages():
    """Тестирование веб-страниц"""
    print_section("ТЕСТИРОВАНИЕ ВЕБ-СТРАНИЦ")
    
    pages = [
        ("/", "Главная страница"),
        ("/articles", "Все статьи"),
        ("/about", "О проекте"),
        ("/contact", "Контакты"),
        ("/feedback", "Обратная связь")
    ]
    
    for endpoint, description in pages:
        print(f"\n{description} ({endpoint}):")
        response = requests.get(f"{BASE_URL}{endpoint}")
        print(f"  Статус: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.find('title')
            if title:
                print(f"  Заголовок страницы: {title.get_text()}")

def test_sort_by_date():
    """Тест сортировки статей по дате"""
    print_section("ТЕСТ: СОРТИРОВКА СТАТЕЙ ПО ДАТЕ")
    
    response = requests.get(f"{BASE_URL}/api/articles/sort/date")
    print(f"URL: GET {BASE_URL}/api/articles/sort/date")
    print(f"Статус: {response.status_code}")
    
    if response.status_code == 200:
        articles = response.json()
        print(f"Найдено статей: {len(articles)}")
        
        if articles:
            print("Последние 3 статьи (самые новые):")
            for i, article in enumerate(articles[:3], 1):
                created_date = article.get('created_date', '')
                date_display = created_date.split('T')[0] if 'T' in created_date else created_date
                print(f"  {i}. {article.get('title')} - {date_display}")

def compare_sources():
    """Сравнение данных из разных источников"""
    print_section("СРАВНЕНИЕ ИСТОЧНИКОВ ДАННЫХ")
    
    api_response = requests.get(f"{BASE_URL}/api/articles")
    json_response = requests.get(f"{BASE_URL}/api/json/articles")
    debug_response = requests.get(f"{BASE_URL}/api/debug/articles")
    
    if api_response.status_code == 200 and json_response.status_code == 200 and debug_response.status_code == 200:
        api_articles = api_response.json()
        json_articles = json_response.json()
        debug_articles = debug_response.json()
        
        print(f"Количество статей в разных источниках:")
        print(f"  API (/api/articles): {len(api_articles)}")
        print(f"  JSON (/api/json/articles): {len(json_articles)}")
        print(f"  Debug (/api/debug/articles): {len(debug_articles)}")
        
        api_ids = [article['id'] for article in api_articles]
        json_ids = [article['id'] for article in json_articles]
        debug_ids = [article['id'] for article in debug_articles]
        
        if set(api_ids) == set(json_ids) == set(debug_ids):
            print("\nВсе источники содержат одинаковые статьи - УСПЕХ!")
        else:
            print("\nОбнаружены различия в источниках данных:")
            if set(api_ids) != set(json_ids):
                print(f"  Разница между API и JSON: {set(api_ids) - set(json_ids)}")
            if set(api_ids) != set(debug_ids):
                print(f"  Разница между API и Debug: {set(api_ids) - set(debug_ids)}")

def main():
    """Основная функция запуска тестов"""
    print("\n" + "=" * 70)
    print("НАЧАЛО ТЕСТИРОВАНИЯ API НОВОСТНОГО БЛОГА")
    print("=" * 70)
    
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        print("Ошибка: BeautifulSoup не установлен. Установите его командой: pip install beautifulsoup4")
        return
    
    test_get_all_articles()
    test_get_article_by_id()
    test_get_articles_by_category()
    test_json_endpoints()
    test_debug_endpoints()
    test_comments_api()
    test_web_pages()
    test_sort_by_date()
    compare_sources()
    
    print_section("ТЕСТЫ С АУТЕНТИФИКАЦИЕЙ")
    
    print("\nСоздание аутентифицированной сессии...")
    session = create_authenticated_session()
    
    new_article_id = test_create_article(session)
    
    if new_article_id:
        test_update_article(session, new_article_id)
        
        print_section("ФИНАЛЬНЫЙ СПИСОК СТАТЕЙ ПОСЛЕ ТЕСТОВ")
        test_get_all_articles(session)
    
    print("\n" + "=" * 70)
    print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("=" * 70)

if __name__ == "__main__":
    main()