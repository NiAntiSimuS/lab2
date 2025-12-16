from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, timedelta
import json
import os
import re
import jwt
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your-secret-key-123-change-this-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///news_blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'jwt-secret-key-123-change-this-too'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Пожалуйста, войдите в систему для доступа к этой странице.'

# Имена JSON файлов
ARTICLES_JSON = 'articles.json'
COMMENTS_JSON = 'comments.json'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    hashed_password = db.Column(db.String(200), nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    articles = db.relationship('Article', backref='author', lazy=True)
    refresh_tokens = db.relationship('RefreshToken', backref='user', lazy=True, cascade='all, delete-orphan')

class RefreshToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(500), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    revoked = db.Column(db.Boolean, default=False)

class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    text = db.Column(db.Text, nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category = db.Column(db.String(50), default='general')
    comments = db.relationship('Comment', backref='article', lazy=True, cascade='all, delete-orphan')

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    article_id = db.Column(db.Integer, db.ForeignKey('article.id'), nullable=False)
    author_name = db.Column(db.String(100), nullable=False)

# JWT Middleware
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Проверяем заголовок Authorization
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]  
            except IndexError:
                return jsonify({'error': 'Некорректный формат заголовка Authorization'}), 401
        
        if not token:
            return jsonify({'error': 'Токен отсутствует'}), 401
        
        try:
            data = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
            
            if data.get('type') != 'access':
                return jsonify({'error': 'Неверный тип токена'}), 401
                
            current_user_id = data['user_id']
            
            # Находим пользователя
            current_user_obj = User.query.get(current_user_id)
            if not current_user_obj:
                return jsonify({'error': 'Пользователь не найден'}), 401
                
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Срок действия токена истек'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Недействительный токен'}), 401
        
        return f(current_user_obj, *args, **kwargs)
    
    return decorated

def create_access_token(user_id):
    """Создание access токена"""
    expires = datetime.utcnow() + app.config['JWT_ACCESS_TOKEN_EXPIRES']
    payload = {
        'user_id': user_id,
        'exp': expires,
        'iat': datetime.utcnow(),
        'type': 'access'
    }
    return jwt.encode(payload, app.config['JWT_SECRET_KEY'], algorithm="HS256")

def create_refresh_token(user_id):
    """Создание refresh токена"""
    expires = datetime.utcnow() + app.config['JWT_REFRESH_TOKEN_EXPIRES']
    
    # Создаем JWT токен
    payload = {
        'user_id': user_id,
        'exp': expires,
        'iat': datetime.utcnow(),
        'type': 'refresh'
    }
    token = jwt.encode(payload, app.config['JWT_SECRET_KEY'], algorithm="HS256")
    
    # Сохраняем refresh токен в базу данных
    refresh_token = RefreshToken(
        token=token,
        user_id=user_id,
        expires_at=expires
    )
    db.session.add(refresh_token)
    db.session.commit()
    
    return token

def revoke_refresh_token(token):
    """Отзыв refresh токена"""
    refresh_token = RefreshToken.query.filter_by(token=token, revoked=False).first()
    if refresh_token:
        refresh_token.revoked = True
        db.session.commit()
        return True
    return False

# Функции для работы с JSON файлами
def init_json_files():
    """Инициализация JSON файлов если их нет"""
    if not os.path.exists(ARTICLES_JSON):
        save_articles_to_json()
    if not os.path.exists(COMMENTS_JSON):
        save_comments_to_json()

def load_json_data(filename):
    """Загрузка данных из JSON файла"""
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    return []

def save_json_data(filename, data):
    """Сохранение данных в JSON файл"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def save_articles_to_json():
    """Сохранение всех статей из БД в JSON файл"""
    articles = Article.query.order_by(Article.created_date.desc()).all()
    articles_data = []
    for article in articles:
        articles_data.append({
            'id': article.id,
            'title': article.title,
            'content': article.text,
            'text': article.text,
            'category': article.category,
            'created_date': article.created_date.isoformat(),
            'author_id': article.user_id,
            'author_name': article.author.name if article.author else 'Неизвестный автор',
            'comments_count': len(article.comments)
        })
    save_json_data(ARTICLES_JSON, articles_data)

def save_comments_to_json():
    """Сохранение всех комментариев из БД в JSON файл"""
    comments = Comment.query.order_by(Comment.date.desc()).all()
    comments_data = []
    for comment in comments:
        comments_data.append({
            'id': comment.id,
            'text': comment.text,
            'author_name': comment.author_name,
            'article_id': comment.article_id,
            'date': comment.date.isoformat()
        })
    save_json_data(COMMENTS_JSON, comments_data)

def save_all_json_files():
    """Сохранение всех данных в JSON файлы"""
    save_articles_to_json()
    save_comments_to_json()

# Функции для преобразования объектов в словари
def article_to_dict(article):
    """Конвертирует объект статьи в словарь для API"""
    return {
        'id': article.id,
        'title': article.title,
        'content': article.text,
        'text': article.text,
        'category': article.category,
        'created_date': article.created_date.isoformat(),
        'author_id': article.user_id,
        'author_name': article.author.name if article.author else 'Неизвестный автор',
        'comments_count': len(article.comments)
    }

def comment_to_dict(comment):
    """Конвертирует объект комментария в словарь для API"""
    return {
        'id': comment.id,
        'text': comment.text,
        'author_name': comment.author_name,
        'article_id': comment.article_id,
        'date': comment.date.isoformat()
    }

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# JWT Authentication Endpoints
@app.route('/api/auth/login', methods=['POST'])
def api_login():
    """Аутентификация пользователя и выдача JWT токенов"""
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email и пароль обязательны'}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    
    if not user or not check_password_hash(user.hashed_password, data['password']):
        return jsonify({'error': 'Неверный email или пароль'}), 401
    
    # Создаем токены
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    
    return jsonify({
        'message': 'Аутентификация успешна',
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': {
            'id': user.id,
            'name': user.name,
            'email': user.email
        }
    })

@app.route('/api/auth/refresh', methods=['POST'])
def api_refresh():
    """Обновление access токена с помощью refresh токена"""
    data = request.get_json()
    
    if not data or not data.get('refresh_token'):
        return jsonify({'error': 'Refresh токен обязателен'}), 400
    
    refresh_token_str = data['refresh_token']
    
    try:
        # Проверяем refresh токен
        payload = jwt.decode(refresh_token_str, app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
        
        if payload['type'] != 'refresh':
            return jsonify({'error': 'Неверный тип токена'}), 401
        
        # Проверяем существование токена в базе данных
        refresh_token = RefreshToken.query.filter_by(
            token=refresh_token_str, 
            revoked=False,
            user_id=payload['user_id']
        ).first()
        
        if not refresh_token:
            return jsonify({'error': 'Refresh токен недействителен или отозван'}), 401
        
        if refresh_token.expires_at < datetime.utcnow():
            refresh_token.revoked = True
            db.session.commit()
            return jsonify({'error': 'Срок действия refresh токена истек'}), 401
        
        # Создаем новый access токен
        new_access_token = create_access_token(payload['user_id'])
        
        return jsonify({
            'message': 'Токен успешно обновлен',
            'access_token': new_access_token
        })
        
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Срок действия refresh токена истек'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Недействительный refresh токен'}), 401

@app.route('/api/auth/logout', methods=['POST'])
@token_required
def api_logout(current_user):
    """Выход из системы и отзыв refresh токена"""
    data = request.get_json()
    
    if not data or not data.get('refresh_token'):
        return jsonify({'error': 'Refresh токен обязателен'}), 400
    
    # Отзываем refresh токен
    if revoke_refresh_token(data['refresh_token']):
        return jsonify({'message': 'Успешный выход из системы'})
    else:
        return jsonify({'error': 'Недействительный refresh токен'}), 400

@app.route('/api/auth/me', methods=['GET'])
@token_required
def api_get_current_user(current_user):
    """Получение информации о текущем пользователе"""
    return jsonify({
        'id': current_user.id,
        'name': current_user.name,
        'email': current_user.email,
        'created_date': current_user.created_date.isoformat()
    })

# Существующие маршруты остаются без изменений
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
            # Обновляем JSON файл после добавления комментария
            save_all_json_files()
            
            flash('Комментарий успешно добавлен!', 'success')
            return redirect(url_for('news_detail', id=id))
        else:
            flash('Пожалуйста, заполните все поля', 'error')
    
    return render_template('news_detail.html', article=article, today=date.today())

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
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Неверный email или пароль', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('index'))

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
            # Обновляем JSON файл после создания статьи
            save_all_json_files()
            
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
        # Обновляем JSON файл после редактирования статьи
        save_all_json_files()
        
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
    
    # Удаляем статью и все связанные комментарии (каскадно)
    db.session.delete(article)
    db.session.commit()
    # Обновляем JSON файл после удаления статьи
    save_all_json_files()
    
    flash('Статья успешно удалена!', 'success')
    return redirect(url_for('index'))

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

# Обновленные API эндпоинты с JWT защитой
@app.route('/api/articles', methods=['POST'])
@token_required
def api_create_article(current_user):
    """Создать статью (защищено JWT)"""
    data = request.get_json()
    
    if not data or not data.get('title') or not data.get('content'):
        return jsonify({'error': 'Название и содержание обязательны'}), 400
    
    article = Article(
        title=data['title'],
        text=data['content'],
        category=data.get('category', 'general'),
        user_id=current_user.id
    )
    
    db.session.add(article)
    db.session.commit()
    # Обновляем JSON файл после создания статьи через API
    save_all_json_files()
    
    return jsonify(article_to_dict(article)), 201

@app.route('/api/articles/<int:id>', methods=['PUT'])
@token_required
def api_update_article(current_user, id):
    """Обновить статью (защищено JWT)"""
    data = request.get_json()
    article = Article.query.get(id)
    
    if not article:
        return jsonify({'error': 'Статья не найдена'}), 404
    
    if not data:
        return jsonify({'error': 'Данные для обновления обязательны'}), 400
    
    # Проверка прав (только автор может редактировать)
    if article.user_id != current_user.id:
        return jsonify({'error': 'Недостаточно прав для редактирования статьи'}), 403
    
    # Обновляем только те поля, которые были переданы
    if 'title' in data:
        article.title = data['title']
    if 'content' in data:
        article.text = data['content']
    if 'category' in data:
        article.category = data['category']
    
    db.session.commit()
    # Обновляем JSON файл после обновления статьи через API
    save_all_json_files()
    
    return jsonify(article_to_dict(article))

@app.route('/api/articles/<int:id>', methods=['DELETE'])
@token_required
def api_delete_article(current_user, id):
    """Удалить статью (защищено JWT)"""
    article = Article.query.get(id)
    
    if not article:
        return jsonify({'error': 'Статья не найдена'}), 404
    
    # Проверка прав (только автор может удалять)
    if article.user_id != current_user.id:
        return jsonify({'error': 'Недостаточно прав для удаления статьи'}), 403
    
    db.session.delete(article)
    db.session.commit()
    # Обновляем JSON файл после удаления статьи через API
    save_all_json_files()
    
    return jsonify({'message': 'Статья удалена', 'article': article_to_dict(article)})

# Эндпоинты для комментариев с JWT защитой
@app.route('/api/comment', methods=['POST'])
@token_required
def api_create_comment(current_user):
    """Создать комментарий (защищено JWT)"""
    data = request.get_json()
    
    if not data or not data.get('text') or not data.get('article_id'):
        return jsonify({'error': 'Текст и ID статьи обязательны'}), 400
    
    # Проверяем существование статьи
    article = Article.query.get(data['article_id'])
    if not article:
        return jsonify({'error': 'Статья не найдена'}), 404
    
    comment = Comment(
        text=data['text'],
        author_name=current_user.name,  # Используем имя пользователя из JWT
        article_id=data['article_id']
    )
    
    db.session.add(comment)
    db.session.commit()
    # Обновляем JSON файл после создания комментария через API
    save_all_json_files()
    
    return jsonify(comment_to_dict(comment)), 201

# Остальные API эндпоинты остаются без изменений
@app.route('/api/articles', methods=['GET'])
def api_articles_list():
    """Получить все статьи (работает с БД)"""
    articles = Article.query.order_by(Article.created_date.desc()).all()
    return jsonify([article_to_dict(article) for article in articles])

@app.route('/api/articles/<int:id>', methods=['GET'])
def api_article_detail(id):
    """Получить статью по ID (работает с БД)"""
    article = Article.query.get(id)
    if article:
        return jsonify(article_to_dict(article))
    return jsonify({'error': 'Статья не найдена'}), 404

@app.route('/api/articles/category/<category>', methods=['GET'])
def api_articles_by_category(category):
    """Получить статьи по категории (работает с БД)"""
    valid_categories = ['technology', 'science', 'culture', 'sports', 'general']
    if category not in valid_categories:
        return jsonify({'error': 'Неверная категория'}), 400
    
    articles = Article.query.filter_by(category=category).order_by(Article.created_date.desc()).all()
    return jsonify([article_to_dict(article) for article in articles])

@app.route('/api/articles/sort/date', methods=['GET'])
def api_articles_sorted_by_date():
    """Получить статьи, отсортированные по дате (работает с БД)"""
    articles = Article.query.order_by(Article.created_date.desc()).all()
    return jsonify([article_to_dict(article) for article in articles])

@app.route('/api/comment', methods=['GET'])
def api_comments_list():
    """Получить все комментарии (работает с БД)"""
    comments = Comment.query.order_by(Comment.date.desc()).all()
    return jsonify([comment_to_dict(comment) for comment in comments])

@app.route('/api/comment/<int:id>', methods=['GET'])
def api_comment_detail(id):
    """Получить комментарий по ID (работает с БД)"""
    comment = Comment.query.get(id)
    if comment:
        return jsonify(comment_to_dict(comment))
    return jsonify({'error': 'Комментарий не найден'}), 404

@app.route('/api/comment/<int:id>', methods=['PUT'])
def api_update_comment(id):
    """Обновить комментарий (работает с БД)"""
    data = request.get_json()
    comment = Comment.query.get(id)
    
    if not comment:
        return jsonify({'error': 'Комментарий не найден'}), 404
    
    if not data or not data.get('text'):
        return jsonify({'error': 'Текст комментария обязателен'}), 400
    
    comment.text = data['text']
    if 'author_name' in data:
        comment.author_name = data['author_name']
    
    db.session.commit()
    # Обновляем JSON файл после обновления комментария через API
    save_all_json_files()
    
    return jsonify(comment_to_dict(comment))

@app.route('/api/comment/<int:id>', methods=['DELETE'])
def api_delete_comment(id):
    """Удалить комментарий (работает с БД)"""
    comment = Comment.query.get(id)
    
    if not comment:
        return jsonify({'error': 'Комментарий не найден'}), 404
    
    db.session.delete(comment)
    db.session.commit()
    # Обновляем JSON файл после удаления комментария через API
    save_all_json_files()
    
    return jsonify({'message': 'Комментарий удален', 'comment': comment_to_dict(comment)})

# API эндпоинты для работы с JSON файлами (для обратной совместимости с тестами)
@app.route('/api/json/articles', methods=['GET'])
def api_json_articles_list():
    """Получить все статьи из JSON файла (для обратной совместимости)"""
    articles_data = load_json_data(ARTICLES_JSON)
    return jsonify(articles_data)

@app.route('/api/json/comments', methods=['GET'])
def api_json_comments_list():
    """Получить все комментарии из JSON файла (для обратной совместимости)"""
    comments_data = load_json_data(COMMENTS_JSON)
    return jsonify(comments_data)

# Отладочные эндпоинты
@app.route('/api/debug/articles')
def debug_articles():
    """Эндпоинт для отладки - показывает статьи из базы данных"""
    articles = Article.query.order_by(Article.created_date.desc()).all()
    articles_data = []
    for article in articles:
        articles_data.append({
            'id': article.id,
            'title': article.title,
            'text': article.text[:100] + '...' if len(article.text) > 100 else article.text,
            'category': article.category,
            'author': article.author.name if article.author else 'Неизвестный автор',
            'author_id': article.user_id,
            'created_date': article.created_date.isoformat(),
            'comments_count': len(article.comments)
        })
    return jsonify(articles_data)

@app.route('/api/debug/comments')
def debug_comments():
    """Эндпоинт для отладки - показывает комментарии из базы данных"""
    comments = Comment.query.order_by(Comment.date.desc()).all()
    comments_data = []
    for comment in comments:
        comments_data.append({
            'id': comment.id,
            'text': comment.text,
            'author_name': comment.author_name,
            'article_id': comment.article_id,
            'article_title': comment.article.title if comment.article else 'Статья удалена',
            'date': comment.date.isoformat()
        })
    return jsonify(comments_data)

@app.route('/api/debug/users')
def debug_users():
    """Эндпоинт для отладки - показывает пользователи из базы данных"""
    users = User.query.all()
    users_data = []
    for user in users:
        users_data.append({
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'articles_count': len(user.articles),
            'created_date': user.created_date.isoformat()
        })
    return jsonify(users_data)

@app.route('/api/debug/save-json', methods=['POST'])
def debug_save_json():
    """Эндпоинт для принудительного сохранения JSON файлов (для отладки)"""
    save_all_json_files()
    return jsonify({'message': 'JSON файлы успешно обновлены'})

# Инициализация базы данных и JSON файлов
with app.app_context():
    db.create_all()
    init_json_files()
    
    # Создаем тестового пользователя, если его нет
    if not User.query.filter_by(email='test@example.com').first():
        test_user = User(
            name='Test User',
            email='test@example.com',
            hashed_password=generate_password_hash('testpassword')
        )
        db.session.add(test_user)
        db.session.commit()
        # Обновляем JSON файлы после создания пользователя
        save_all_json_files()
        print("Создан тестовый пользователь: test@example.com / testpassword")

if __name__ == '__main__':
    app.run(debug=True)
