from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime, date
import re

app = Flask(__name__)
app.secret_key = 'your-secret-key-123'

# Моковые данные статей
articles = [
    {
        'id': 1,
        'title': 'Искусственный интеллект в современном мире',
        'content': 'Искусственный интеллект продолжает трансформировать различные отрасли...',
        'date': date.today(),
        'published': True
    },
    {
        'id': 2,
        'title': 'Новые тенденции в веб-разработке',
        'content': 'Современная веб-разработка постоянно развивается...',
        'date': date(2024, 1, 10),
        'published': True
    },
    {
        'id': 3,
        'title': 'Будущее мобильных технологий',
        'content': 'Мобильные технологии становятся все более интегрированными в нашу жизнь...',
        'date': date.today(),
        'published': True
    },
    {
        'id': 4,
        'title': 'Устойчивое развитие и технологии',
        'content': 'Технологии играют ключевую роль в достижении целей устойчивого развития...',
        'date': date(2024, 1, 8),
        'published': True
    },
    {
        'id': 5,
        'title': 'Кибербезопасность в 2024 году',
        'content': 'С ростом цифровизации кибербезопасность становится все более важной...',
        'date': date.today(),
        'published': True
    }
]

@app.route('/')
def index():
    today = date.today()
    return render_template('index.html', articles=articles, today=today)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        
        # Валидация
        errors = []
        if not name:
            errors.append('Имя обязательно для заполнения')
        if not email:
            errors.append('Email обязателен для заполнения')
        elif not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            errors.append('Введите корректный email')
        if not message:
            errors.append('Сообщение обязательно для заполнения')
        
        if errors:
            for error in errors:
                flash(error, 'error')
        else:
            flash('Сообщение успешно отправлено! Спасибо за вашу обратную связь.', 'success')
            return redirect(url_for('feedback'))
    
    return render_template('feedback.html')

@app.route('/news/<int:id>')
def news_detail(id):
    article = next((article for article in articles if article['id'] == id), None)
    if article:
        today = date.today()
        return render_template('news_detail.html', article=article, today=today)
    else:
        return "Статья не найдена", 404

if __name__ == '__main__':
    app.run(debug=True)