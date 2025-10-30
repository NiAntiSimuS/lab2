from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
import json
import os
import re

app = Flask(__name__)
app.secret_key = 'your-secret-key-123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///news_blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Инициализация расширений
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Пожалуйста, войдите в систему для доступа к этой странице.'

# Модели для SQL базы (Лаба 2)
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    hashed_password = db.Column(db.String(200), nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    articles = db.relationship('Article', backref='author', lazy=True)

class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    text = db.Column(db.Text, nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category = db.Column(db.String(50), default='general')
    comments = db.relationship('Comment', backref='article', lazy=True)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    article_id = db.Column(db.Integer, db.ForeignKey('article.id'), nullable=False)
    author_name = db.Column(db.String(100), nullable=False)

# JSON файлы для API (Лаба 4)
ARTICLES_JSON = 'articles.json'
COMMENTS_JSON = 'comments.json'

def load_json_data(filename):
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_json_data(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Моковые данные для демонстрации (можно удалить после наполнения БД)
articles = [
    {
        'id': 1,
        'title': 'Искусственный интеллект в современном мире',
        'content': 'Искусственный интеллект продолжает трансформировать различные отрасли...',
        'date': date.today(),
        'published': True
    }
]

# Маршруты для веб-интерфейса (SQL)
@app.route('/')
def index():
    articles = Article.query.order_by(Article.created_date.desc()).all()
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

@app.route('/news/<int:id>', methods=['GET', 'POST'])
def news_detail(id):
    article = Article.query.get_or_404(id)
    
    if request.method == 'POST':
        author_name = request.form.get('author_name')
        comment_text = request.form.get('comment_text')
        
        if author_name and comment_text:
            comment = Comment(
                text=comment_text,
                author_name=author_name,
                article_id=id
            )
            db.session.add(comment)
            db.session.commit()
            flash('Комментарий успешно добавлен!', 'success')
            return redirect(url_for('news_detail', id=id))
        else:
            flash('Пожалуйста, заполните все поля', 'error')
    
    return render_template('news_detail.html', article=article, today=date.today())

# Аутентификация
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(email=email).first():
            flash('Пользователь с таким email уже существует', 'error')
            return render_template('register.html')
        
        user = User(
            name=name,
            email=email,
            hashed_password=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        
        flash('Регистрация успешна! Теперь вы можете войти.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.hashed_password, password):
            login_user(user)
            flash('Вы успешно вошли в систему!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Неверный email или пароль', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('index'))

# CRUD для статей
@app.route('/create-article', methods=['GET', 'POST'])
@login_required
def create_article():
    if request.method == 'POST':
        title = request.form.get('title')
        text = request.form.get('text')
        category = request.form.get('category', 'general')
        
        if title and text:
            article = Article(
                title=title,
                text=text,
                category=category,
                user_id=current_user.id
            )
            db.session.add(article)
            db.session.commit()
            flash('Статья успешно создана!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Пожалуйста, заполните все обязательные поля', 'error')
    
    return render_template('create_article.html')

@app.route('/edit-article/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_article(id):
    article = Article.query.get_or_404(id)
    
    if article.author != current_user:
        flash('Вы можете редактировать только свои статьи', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        article.title = request.form.get('title')
        article.text = request.form.get('text')
        article.category = request.form.get('category', 'general')
        db.session.commit()
        flash('Статья успешно обновлена!', 'success')
        return redirect(url_for('news_detail', id=id))
    
    return render_template('edit_article.html', article=article)

@app.route('/delete-article/<int:id>')
@login_required
def delete_article(id):
    article = Article.query.get_or_404(id)
    
    if article.author != current_user:
        flash('Вы можете удалять только свои статьи', 'error')
        return redirect(url_for('index'))
    
    # Удаляем связанные комментарии
    Comment.query.filter_by(article_id=id).delete()
    db.session.delete(article)
    db.session.commit()
    flash('Статья успешно удалена!', 'success')
    return redirect(url_for('index'))

# Страницы со статьями и фильтрацией
@app.route('/articles')
def articles_list():
    articles = Article.query.order_by(Article.created_date.desc()).all()
    return render_template('articles_list.html', articles=articles)

@app.route('/articles/<category>')
def articles_by_category(category):
    valid_categories = ['technology', 'science', 'culture', 'sports', 'general']
    if category not in valid_categories:
        return "Категория не найдена", 404
    
    articles = Article.query.filter_by(category=category).order_by(Article.created_date.desc()).all()
    return render_template('articles_list.html', articles=articles, category=category)

# API маршруты для работы с JSON (Лаба 4)
@app.route('/api/articles', methods=['GET'])
def api_articles_list():
    articles_data = load_json_data(ARTICLES_JSON)
    return jsonify(articles_data)

@app.route('/api/articles/<int:id>', methods=['GET'])
def api_article_detail(id):
    articles_data = load_json_data(ARTICLES_JSON)
    article = next((a for a in articles_data if a['id'] == id), None)
    if article:
        return jsonify(article)
    return jsonify({'error': 'Статья не найдена'}), 404

@app.route('/api/articles/category/<category>', methods=['GET'])
def api_articles_by_category(category):
    articles_data = load_json_data(ARTICLES_JSON)
    filtered_articles = [a for a in articles_data if a.get('category') == category]
    return jsonify(filtered_articles)

@app.route('/api/articles/sort/date', methods=['GET'])
def api_articles_sorted_by_date():
    articles_data = load_json_data(ARTICLES_JSON)
    sorted_articles = sorted(articles_data, key=lambda x: x.get('created_date', ''), reverse=True)
    return jsonify(sorted_articles)

@app.route('/api/articles', methods=['POST'])
def api_create_article():
    data = request.get_json()
    
    # Валидация
    if not data or not data.get('title') or not data.get('content'):
        return jsonify({'error': 'Название и содержание обязательны'}), 400
    
    articles_data = load_json_data(ARTICLES_JSON)
    new_id = max([a.get('id', 0) for a in articles_data], default=0) + 1
    
    new_article = {
        'id': new_id,
        'title': data['title'],
        'content': data['content'],
        'category': data.get('category', 'general'),
        'created_date': datetime.now().isoformat()
    }
    
    articles_data.append(new_article)
    save_json_data(ARTICLES_JSON, articles_data)
    return jsonify(new_article), 201

@app.route('/api/articles/<int:id>', methods=['PUT'])
def api_update_article(id):
    data = request.get_json()
    articles_data = load_json_data(ARTICLES_JSON)
    
    article_index = next((i for i, a in enumerate(articles_data) if a['id'] == id), None)
    if article_index is None:
        return jsonify({'error': 'Статья не найдена'}), 404
    
    # Валидация
    if not data or not data.get('title') or not data.get('content'):
        return jsonify({'error': 'Название и содержание обязательны'}), 400
    
    articles_data[article_index].update({
        'title': data['title'],
        'content': data['content'],
        'category': data.get('category', articles_data[article_index].get('category', 'general'))
    })
    
    save_json_data(ARTICLES_JSON, articles_data)
    return jsonify(articles_data[article_index])

@app.route('/api/articles/<int:id>', methods=['DELETE'])
def api_delete_article(id):
    articles_data = load_json_data(ARTICLES_JSON)
    article_index = next((i for i, a in enumerate(articles_data) if a['id'] == id), None)
    
    if article_index is None:
        return jsonify({'error': 'Статья не найдена'}), 404
    
    deleted_article = articles_data.pop(article_index)
    save_json_data(ARTICLES_JSON, articles_data)
    return jsonify({'message': 'Статья удалена', 'article': deleted_article})

# API для комментариев (JSON)
@app.route('/api/comment', methods=['GET'])
def api_comments_list():
    comments_data = load_json_data(COMMENTS_JSON)
    return jsonify(comments_data)

@app.route('/api/comment/<int:id>', methods=['GET'])
def api_comment_detail(id):
    comments_data = load_json_data(COMMENTS_JSON)
    comment = next((c for c in comments_data if c['id'] == id), None)
    if comment:
        return jsonify(comment)
    return jsonify({'error': 'Комментарий не найдена'}), 404

@app.route('/api/comment', methods=['POST'])
def api_create_comment():
    data = request.get_json()
    
    if not data or not data.get('text') or not data.get('author_name') or not data.get('article_id'):
        return jsonify({'error': 'Текст, имя автора и ID статьи обязательны'}), 400
    
    comments_data = load_json_data(COMMENTS_JSON)
    new_id = max([c.get('id', 0) for c in comments_data], default=0) + 1
    
    new_comment = {
        'id': new_id,
        'text': data['text'],
        'author_name': data['author_name'],
        'article_id': data['article_id'],
        'date': datetime.now().isoformat()
    }
    
    comments_data.append(new_comment)
    save_json_data(COMMENTS_JSON, comments_data)
    return jsonify(new_comment), 201

@app.route('/api/comment/<int:id>', methods=['PUT'])
def api_update_comment(id):
    data = request.get_json()
    comments_data = load_json_data(COMMENTS_JSON)
    
    comment_index = next((i for i, c in enumerate(comments_data) if c['id'] == id), None)
    if comment_index is None:
        return jsonify({'error': 'Комментарий не найден'}), 404
    
    if not data or not data.get('text'):
        return jsonify({'error': 'Текст комментария обязателен'}), 400
    
    comments_data[comment_index].update({
        'text': data['text'],
        'author_name': data.get('author_name', comments_data[comment_index].get('author_name'))
    })
    
    save_json_data(COMMENTS_JSON, comments_data)
    return jsonify(comments_data[comment_index])

@app.route('/api/comment/<int:id>', methods=['DELETE'])
def api_delete_comment(id):
    comments_data = load_json_data(COMMENTS_JSON)
    comment_index = next((i for i, c in enumerate(comments_data) if c['id'] == id), None)
    
    if comment_index is None:
        return jsonify({'error': 'Комментарий не найден'}), 404
    
    deleted_comment = comments_data.pop(comment_index)
    save_json_data(COMMENTS_JSON, comments_data)
    return jsonify({'message': 'Комментарий удален', 'comment': deleted_comment})

# Инициализация базы данных
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)