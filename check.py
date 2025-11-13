import requests
import json
import pytest

# Базовый URL вашего приложения
BASE_URL = 'http://localhost:5000'

# Тестовые данные
TEST_ARTICLE = {
    'title': 'Тестовая статья',
    'content': 'Это содержимое тестовой статьи',
    'category': 'technology'
}

TEST_COMMENT = {
    'text': 'Тестовый комментарий',
    'author_name': 'Тестовый автор',
    'article_id': 1
}

class TestNewsBlogAPI:
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.session = requests.Session()
    
    def teardown_method(self):
        """Очистка после каждого теста"""
        self.session.close()

    # Тесты для статей
    def test_get_all_articles(self):
        """Тест получения всех статей"""
        response = self.session.get(f'{BASE_URL}/api/articles')
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        print("GET /api/articles - Успешно")

    def test_create_article(self):
        """Тест создания статьи"""
        response = self.session.post(
            f'{BASE_URL}/api/articles',
            json=TEST_ARTICLE,
            headers={'Content-Type': 'application/json'}
        )
        assert response.status_code == 201
        data = response.json()
        assert data['title'] == TEST_ARTICLE['title']
        assert data['content'] == TEST_ARTICLE['content']
        assert 'id' in data
        print("POST /api/articles - Успешно")
        return data['id']  # Возвращаем ID для использования в других тестах

    def test_create_article_validation(self):
        """Тест валидации при создании статьи"""
        # Отправка пустых данных
        response = self.session.post(
            f'{BASE_URL}/api/articles',
            json={},
            headers={'Content-Type': 'application/json'}
        )
        assert response.status_code == 400
        print("POST /api/articles (валидация) - Успешно")

    def test_get_article_by_id(self):
        """Тест получения статьи по ID"""
        # Сначала создаем статью
        article_id = self.test_create_article()
        
        # Получаем статью по ID
        response = self.session.get(f'{BASE_URL}/api/articles/{article_id}')
        assert response.status_code == 200
        data = response.json()
        assert data['id'] == article_id
        print(f"GET /api/articles/{article_id} - Успешно")

    def test_get_nonexistent_article(self):
        """Тест получения несуществующей статьи"""
        response = self.session.get(f'{BASE_URL}/api/articles/9999')
        assert response.status_code == 404
        print("GET /api/articles/9999 (несуществующая) - Успешно")

    def test_update_article(self):
        """Тест обновления статьи"""
        # Сначала создаем статью
        article_id = self.test_create_article()
        
        # Обновляем статью
        updated_data = {
            'title': 'Обновленная статья',
            'content': 'Обновленное содержимое',
            'category': 'science'
        }
        
        response = self.session.put(
            f'{BASE_URL}/api/articles/{article_id}',
            json=updated_data,
            headers={'Content-Type': 'application/json'}
        )
        assert response.status_code == 200
        data = response.json()
        assert data['title'] == updated_data['title']
        assert data['content'] == updated_data['content']
        print(f"PUT /api/articles/{article_id} - Успешно")

    def test_update_article_validation(self):
        """Тест валидации при обновлении статьи"""
        # Сначала создаем статью
        article_id = self.test_create_article()
        
        # Пытаемся обновить с пустыми данными
        response = self.session.put(
            f'{BASE_URL}/api/articles/{article_id}',
            json={},
            headers={'Content-Type': 'application/json'}
        )
        assert response.status_code == 400
        print(f"PUT /api/articles/{article_id} (валидация) - Успешно")

    def test_delete_article(self):
        """Тест удаления статьи"""
        # Сначала создаем статью
        article_id = self.test_create_article()
        
        # Удаляем статью
        response = self.session.delete(f'{BASE_URL}/api/articles/{article_id}')
        assert response.status_code == 200
        data = response.json()
        assert data['message'] == 'Статья удалена'
        print(f"DELETE /api/articles/{article_id} - Успешно")

    def test_get_articles_by_category(self):
        """Тест получения статей по категории"""
        response = self.session.get(f'{BASE_URL}/api/articles/category/technology')
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        print("GET /api/articles/category/technology - Успешно")

    def test_get_articles_sorted_by_date(self):
        """Тест получения статей отсортированных по дате"""
        response = self.session.get(f'{BASE_URL}/api/articles/sort/date')
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Проверяем что статьи отсортированы (первая статья должна быть новее)
        if len(data) > 1:
            dates = [article.get('created_date', '') for article in data]
            assert dates == sorted(dates, reverse=True)
        print("GET /api/articles/sort/date - Успешно")

    # Тесты для комментариев
    def test_get_all_comments(self):
        """Тест получения всех комментариев"""
        response = self.session.get(f'{BASE_URL}/api/comment')
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        print("GET /api/comment - Успешно")

    def test_create_comment(self):
        """Тест создания комментария"""
        # Сначала создаем статью для комментария
        article_id = self.test_create_article()
        
        TEST_COMMENT['article_id'] = article_id
        
        response = self.session.post(
            f'{BASE_URL}/api/comment',
            json=TEST_COMMENT,
            headers={'Content-Type': 'application/json'}
        )
        assert response.status_code == 201
        data = response.json()
        assert data['text'] == TEST_COMMENT['text']
        assert data['author_name'] == TEST_COMMENT['author_name']
        assert 'id' in data
        print("POST /api/comment - Успешно")
        return data['id']

    def test_create_comment_validation(self):
        """Тест валидации при создании комментария"""
        response = self.session.post(
            f'{BASE_URL}/api/comment',
            json={},
            headers={'Content-Type': 'application/json'}
        )
        assert response.status_code == 400
        print("POST /api/comment (валидация) - Успешно")

    def test_get_comment_by_id(self):
        """Тест получения комментария по ID"""
        # Сначала создаем комментарий
        comment_id = self.test_create_comment()
        
        response = self.session.get(f'{BASE_URL}/api/comment/{comment_id}')
        assert response.status_code == 200
        data = response.json()
        assert data['id'] == comment_id
        print(f"GET /api/comment/{comment_id} - Успешно")

    def test_update_comment(self):
        """Тест обновления комментария"""
        # Сначала создаем комментарий
        comment_id = self.test_create_comment()
        
        updated_comment = {
            'text': 'Обновленный комментарий',
            'author_name': 'Новое имя'
        }
        
        response = self.session.put(
            f'{BASE_URL}/api/comment/{comment_id}',
            json=updated_comment,
            headers={'Content-Type': 'application/json'}
        )
        assert response.status_code == 200
        data = response.json()
        assert data['text'] == updated_comment['text']
        print(f"PUT /api/comment/{comment_id} - Успешно")

    def test_delete_comment(self):
        """Тест удаления комментария"""
        # Сначала создаем комментарий
        comment_id = self.test_create_comment()
        
        response = self.session.delete(f'{BASE_URL}/api/comment/{comment_id}')
        assert response.status_code == 200
        data = response.json()
        assert data['message'] == 'Комментарий удален'
        print(f"DELETE /api/comment/{comment_id} - Успешно")

    # Интеграционные тесты
    def test_article_with_comments_flow(self):
        """Интеграционный тест: создание статьи и комментариев к ней"""
        # Создаем статью
        article_response = self.session.post(
            f'{BASE_URL}/api/articles',
            json=TEST_ARTICLE,
            headers={'Content-Type': 'application/json'}
        )
        assert article_response.status_code == 201
        article_id = article_response.json()['id']
        
        # Создаем несколько комментариев к статье
        comments_data = [
            {'text': 'Первый комментарий', 'author_name': 'Автор 1', 'article_id': article_id},
            {'text': 'Второй комментарий', 'author_name': 'Автор 2', 'article_id': article_id}
        ]
        
        for comment_data in comments_data:
            response = self.session.post(
                f'{BASE_URL}/api/comment',
                json=comment_data,
                headers={'Content-Type': 'application/json'}
            )
            assert response.status_code == 201
        
        # Проверяем что комментарии создались
        comments_response = self.session.get(f'{BASE_URL}/api/comment')
        assert comments_response.status_code == 200
        comments = comments_response.json()
        
        # Фильтруем комментарии для нашей статьи
        article_comments = [c for c in comments if c.get('article_id') == article_id]
        assert len(article_comments) == 2
        
        print("Интеграционный тест статьи с комментариями - Успешно")

def run_all_tests():
    """Функция для запуска всех тестов"""
    tester = TestNewsBlogAPI()
    
    # Список тестов для выполнения
    test_methods = [
        'test_get_all_articles',
        'test_create_article',
        'test_create_article_validation',
        'test_get_article_by_id',
        'test_get_nonexistent_article',
        'test_update_article',
        'test_update_article_validation',
        'test_delete_article',
        'test_get_articles_by_category',
        'test_get_articles_sorted_by_date',
        'test_get_all_comments',
        'test_create_comment',
        'test_create_comment_validation',
        'test_get_comment_by_id',
        'test_update_comment',
        'test_delete_comment',
        'test_article_with_comments_flow'
    ]
    
    print("Запуск тестов API новостного блога...")
    print("=" * 50)
    
    for method_name in test_methods:
        try:
            method = getattr(tester, method_name)
            tester.setup_method()
            method()
            tester.teardown_method()
            print(f"✓ {method_name} - ПРОЙДЕН")
        except Exception as e:
            print(f"✗ {method_name} - ОШИБКА: {str(e)}")
    
    print("=" * 50)
    print("Тестирование завершено!")

if __name__ == '__main__':
    # Запуск всех тестов
    run_all_tests()