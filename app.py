from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
from sqlalchemy import or_

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@app.context_processor
def utility_processor():
    from datetime import datetime
    def get_cart_count():
        if current_user.is_authenticated:
            return Cart.query.filter_by(user_id=current_user.id).count()
        return 0
    
    def get_wishlist_count():
        if current_user.is_authenticated:
            return Wishlist.query.filter_by(user_id=current_user.id).count()
        return 0
    
    def get_tracking_count():
        if current_user.is_authenticated:
            return Tracking.query.filter_by(user_id=current_user.id).count()
        return 0
    
    return dict(
        cart_count=get_cart_count,
        wishlist_count=get_wishlist_count,
        tracking_count=get_tracking_count,
        now=datetime.now
    )

# ========== МОДЕЛІ БАЗИ ДАНИХ ==========

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='reader')  # admin, librarian, reader
    full_name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer)
    publisher = db.Column(db.String(100))
    genre = db.Column(db.String(100))
    total_copies = db.Column(db.Integer, default=1)
    available_copies = db.Column(db.Integer, default=1)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

class Reader(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    card_number = db.Column(db.String(20), unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    address = db.Column(db.Text)
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

class Loan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    reader_id = db.Column(db.Integer, db.ForeignKey('reader.id'), nullable=False)
    librarian_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    loan_date = db.Column(db.Date, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    return_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='active')  # active, returned, overdue
    
    book = db.relationship('Book', backref='loans')
    reader = db.relationship('Reader', backref='loans')
    librarian = db.relationship('User', backref='loans_given')

class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

class LibraryInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    working_hours = db.Column(db.String(500))
    contacts = db.Column(db.String(500))
    history = db.Column(db.Text)
    address = db.Column(db.String(300))

class Wishlist(db.Model):
    """Закладки (книги, які користувач хоче прочитати)"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='wishlist_items')
    book = db.relationship('Book', backref='wishlist_by')

class Cart(db.Model):
    """Кошик (книги, які користувач хоче забронювати)"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='cart_items')
    book = db.relationship('Book', backref='in_cart_by')

class Tracking(db.Model):
    """Відстеження наявності книг"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    is_available = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_notified = db.Column(db.DateTime)
    
    user = db.relationship('User', backref='tracking_items')
    book = db.relationship('Book', backref='tracked_by')

class UserLoanHistory(db.Model):
    """Історія бронювань користувача (додатково до Loan)"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    loan_id = db.Column(db.Integer, db.ForeignKey('loan.id'), nullable=False)
    extended = db.Column(db.Boolean, default=False)  # Чи було продовження
    extended_until = db.Column(db.Date)  # Нова дата повернення після продовження
    
    user = db.relationship('User', backref='loan_history')
    loan = db.relationship('Loan', backref='user_history')

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# ========== ДОПОМІЖНІ ФУНКЦІЇ ==========

def admin_required(f):
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Доступ заборонено. Потрібні права адміністратора.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def librarian_required(f):
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ['admin', 'librarian']:
            flash('Доступ заборонено. Потрібні права бібліотекаря.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# ========== МАРШРУТИ (ROUTES) ==========

@app.route('/')
def index():
    news_list = News.query.filter_by(is_active=True).order_by(News.created_at.desc()).limit(5).all()
    new_books = Book.query.order_by(Book.added_at.desc()).limit(6).all()
    library_info = LibraryInfo.query.first()
    return render_template('index.html', 
                         news=news_list, 
                         new_books=new_books,
                         info=library_info)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash(f'Вітаємо, {user.full_name}!', 'success')
            if user.role == 'reader':
                return redirect(url_for('profile'))
            else:
                return redirect(url_for('dashboard'))
        else:
            flash('Невірне ім\'я користувача або пароль', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Ви вийшли з системи', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'reader':
        return redirect(url_for('profile'))
    
    books_count = Book.query.count()
    readers_count = Reader.query.count()
    active_loans = Loan.query.filter_by(status='active').count()
    overdue_loans = Loan.query.filter(Loan.status == 'active', Loan.due_date < datetime.now().date()).count()
    
    recent_loans = Loan.query.order_by(Loan.loan_date.desc()).limit(5).all()
    
    return render_template('dashboard.html', 
                         books_count=books_count,
                         readers_count=readers_count,
                         active_loans=active_loans,
                         overdue_loans=overdue_loans,
                         recent_loans=recent_loans)

# ========== КНИГИ ==========

@app.route('/books')
def books():
    # Отримуємо параметри з URL
    search = request.args.get('search', '')
    author = request.args.get('author', '')
    genre = request.args.get('genre', '')
    year_from = request.args.get('year_from', '', type=int)
    year_to = request.args.get('year_to', '', type=int)
    available = request.args.get('available', '')
    sort_by = request.args.get('sort_by', 'title')
    order = request.args.get('order', 'asc')
    
    # Базовий запит
    query = Book.query
    
    # Фільтри
    if search:
        query = query.filter(
            or_(
                Book.title.ilike(f'%{search}%'),
                Book.author.ilike(f'%{search}%')
            )
        )
    
    if author:
        query = query.filter(Book.author.ilike(f'%{author}%'))
    
    if genre:
        query = query.filter(Book.genre == genre)
    
    if year_from:
        query = query.filter(Book.year >= year_from)
    
    if year_to:
        query = query.filter(Book.year <= year_to)
    
    if available == 'yes':
        query = query.filter(Book.available_copies > 0)
    elif available == 'no':
        query = query.filter(Book.available_copies == 0)
    
    # Сортування
    if sort_by == 'title':
        query = query.order_by(Book.title.asc() if order == 'asc' else Book.title.desc())
    elif sort_by == 'author':
        query = query.order_by(Book.author.asc() if order == 'asc' else Book.author.desc())
    elif sort_by == 'year':
        query = query.order_by(Book.year.asc() if order == 'asc' else Book.year.desc())
    elif sort_by == 'genre':
        query = query.order_by(Book.genre.asc() if order == 'asc' else Book.genre.desc())
    elif sort_by == 'available':
        query = query.order_by(Book.available_copies.asc() if order == 'asc' else Book.available_copies.desc())
    
    books_list = query.all()
    
    # Отримуємо списки для фільтрів
    authors = db.session.query(Book.author).distinct().all()
    authors = [a[0] for a in authors if a[0]]
    
    genres = db.session.query(Book.genre).distinct().all()
    genres = [g[0] for g in genres if g[0]]
    
    return render_template('books.html', 
                         books=books_list, 
                         search=search,
                         author=author,
                         genre=genre,
                         year_from=year_from,
                         year_to=year_to,
                         available=available,
                         sort_by=sort_by,
                         order=order,
                         authors=authors,
                         genres=genres)

@app.route('/book/add', methods=['GET', 'POST'])
@librarian_required
def add_book():
    if request.method == 'POST':
        book = Book(
            title=request.form['title'],
            author=request.form['author'],
            year=request.form.get('year', type=int),
            publisher=request.form['publisher'],
            genre=request.form.get('genre'),
            total_copies=request.form.get('total_copies', type=int),
            available_copies=request.form.get('total_copies', type=int)
        )
        db.session.add(book)
        db.session.commit()
        flash('Книгу успішно додано!', 'success')
        return redirect(url_for('books'))
    return render_template('book_form.html', title='Додати книгу')

@app.route('/book/edit/<int:id>', methods=['GET', 'POST'])
@librarian_required
def edit_book(id):
    book = Book.query.get_or_404(id)
    if request.method == 'POST':
        book.title = request.form['title']
        book.author = request.form['author']
        book.year = request.form.get('year', type=int)
        book.publisher = request.form['publisher']
        book.genre = request.form.get('genre')
        old_copies = book.total_copies
        new_copies = request.form.get('total_copies', type=int)
        book.total_copies = new_copies
        book.available_copies = book.available_copies + (new_copies - old_copies)
        db.session.commit()
        flash('Книгу оновлено!', 'success')
        return redirect(url_for('books'))
    return render_template('book_form.html', title='Редагувати книгу', book=book)

@app.route('/book/delete/<int:id>')
@admin_required
def delete_book(id):
    book = Book.query.get_or_404(id)
    if book.loans:
        flash('Неможливо видалити книгу, яка видавалась читачам!', 'danger')
    else:
        db.session.delete(book)
        db.session.commit()
        flash('Книгу видалено!', 'success')
    return redirect(url_for('books'))

# ========== ЧИТАЧІ ==========

@app.route('/readers')
@login_required
def readers():
    readers_list = Reader.query.all()
    return render_template('readers.html', readers=readers_list)

@app.route('/reader/add', methods=['GET', 'POST'])
@librarian_required
def add_reader():
    if request.method == 'POST':
        reader = Reader(
            card_number=request.form['card_number'],
            full_name=request.form['full_name'],
            phone=request.form.get('phone'),
            email=request.form.get('email'),
            address=request.form.get('address')
        )
        db.session.add(reader)
        db.session.commit()
        flash('Читача успішно додано!', 'success')
        return redirect(url_for('readers'))
    return render_template('reader_form.html', title='Додати читача')

@app.route('/reader/edit/<int:id>', methods=['GET', 'POST'])
@librarian_required
def edit_reader(id):
    reader = Reader.query.get_or_404(id)
    if request.method == 'POST':
        reader.card_number = request.form['card_number']
        reader.full_name = request.form['full_name']
        reader.phone = request.form.get('phone')
        reader.email = request.form.get('email')
        reader.address = request.form.get('address')
        db.session.commit()
        flash('Дані читача оновлено!', 'success')
        return redirect(url_for('readers'))
    return render_template('reader_form.html', title='Редагувати читача', reader=reader)

@app.route('/reader/delete/<int:id>')
@admin_required
def delete_reader(id):
    reader = Reader.query.get_or_404(id)
    if reader.loans:
        flash('Неможливо видалити читача, який має книги на руках!', 'danger')
    else:
        db.session.delete(reader)
        db.session.commit()
        flash('Читача видалено!', 'success')
    return redirect(url_for('readers'))

# ========== ВИДАЧА КНИГ ==========

@app.route('/loans')
@login_required
def loans():
    from datetime import datetime
    active_loans = Loan.query.filter_by(status='active').all()
    history = Loan.query.filter_by(status='returned').order_by(Loan.return_date.desc()).limit(20).all()
    return render_template('loans.html', 
                         active_loans=active_loans, 
                         history=history,
                         now=datetime.now())   # Додаємо now замість today

@app.route('/loan/create', methods=['GET', 'POST'])
@librarian_required
def create_loan():
    if request.method == 'POST':
        book_id = request.form['book_id']
        reader_id = request.form['reader_id']
        days = request.form.get('days', 14, type=int)
        
        book = Book.query.get(book_id)
        reader = Reader.query.get(reader_id)
        
        if not book or not reader:
            flash('Книгу або читача не знайдено', 'danger')
            return redirect(url_for('create_loan'))
        
        if book.available_copies < 1:
            flash(f'Книги "{book.title}" немає в наявності!', 'danger')
            return redirect(url_for('create_loan'))
        
        loan = Loan(
            book_id=book_id,
            reader_id=reader_id,
            librarian_id=current_user.id,
            loan_date=datetime.now().date(),
            due_date=datetime.now().date() + timedelta(days=days)
        )
        book.available_copies -= 1
        
        db.session.add(loan)
        db.session.commit()
        flash(f'Книгу "{book.title}" видано читачу "{reader.full_name}"', 'success')
        return redirect(url_for('loans'))
    
    books_list = Book.query.filter(Book.available_copies > 0).all()
    readers_list = Reader.query.all()
    return render_template('loan_form.html', books=books_list, readers=readers_list)

@app.route('/loan/return/<int:id>')
@librarian_required
def return_loan(id):
    loan = Loan.query.get_or_404(id)
    if loan.status == 'active':
        loan.status = 'returned'
        loan.return_date = datetime.now().date()
        loan.book.available_copies += 1
        db.session.commit()
        flash(f'Книгу "{loan.book.title}" повернуто!', 'success')
    return redirect(url_for('loans'))

# ========== ЗВІТИ ==========

@app.route('/reports')
@login_required
def reports():
    from datetime import datetime
    overdue_loans = Loan.query.filter(
        Loan.status == 'active', 
        Loan.due_date < datetime.now().date()
    ).all()
    
    popular_books = db.session.query(
        Book.title, db.func.count(Loan.id).label('count')
    ).join(Loan).group_by(Book.id).order_by(db.desc('count')).limit(10).all()
    
    return render_template('reports.html', 
                         overdue_loans=overdue_loans, 
                         popular_books=popular_books,
                         now=datetime.now())

@app.route('/profile')
@login_required
def profile():
    # Отримуємо дані користувача
    from datetime import datetime
    wishlist = Wishlist.query.filter_by(user_id=current_user.id).all()
    cart = Cart.query.filter_by(user_id=current_user.id).all()
    tracking = Tracking.query.filter_by(user_id=current_user.id).all()
    
    # Активні бронювання користувача
    user_loans = Loan.query.filter(
        Loan.reader_id == current_user.id,
        Loan.status == 'active'
    ).all()
    
    # Історія бронювань
    loan_history = Loan.query.filter(
        Loan.reader_id == current_user.id,
        Loan.status == 'returned'
    ).order_by(Loan.return_date.desc()).limit(10).all()
    
    # Перевірка боргів
    has_debt = any(loan.due_date < datetime.now().date() for loan in user_loans)
    
    return render_template('profile.html',
                         wishlist=wishlist,
                         cart=cart,
                         tracking=tracking,
                         user_loans=user_loans,
                         loan_history=loan_history,
                         has_debt=has_debt,
                         now=datetime.now())

# ========== ЗАКЛАДКИ ==========

@app.route('/wishlist/add/<int:book_id>')
@login_required
def add_to_wishlist(book_id):
    # Перевіряємо, чи вже є в закладках
    existing = Wishlist.query.filter_by(user_id=current_user.id, book_id=book_id).first()
    if not existing:
        wishlist_item = Wishlist(user_id=current_user.id, book_id=book_id)
        db.session.add(wishlist_item)
        db.session.commit()
        flash('Книгу додано до закладок!', 'success')
    else:
        flash('Книга вже у ваших закладках', 'info')
    return redirect(request.referrer or url_for('books'))

@app.route('/wishlist/remove/<int:book_id>')
@login_required
def remove_from_wishlist(book_id):
    item = Wishlist.query.filter_by(user_id=current_user.id, book_id=book_id).first()
    if item:
        db.session.delete(item)
        db.session.commit()
        flash('Книгу видалено із закладок', 'success')
    return redirect(url_for('profile'))

# ========== КОШИК ==========

@app.route('/cart/add/<int:book_id>')
@login_required
def add_to_cart(book_id):
    # Перевіряємо, чи книга доступна
    book = Book.query.get(book_id)
    if book.available_copies < 1:
        flash('На жаль, ця книга вже недоступна для бронювання', 'danger')
        return redirect(request.referrer or url_for('books'))
    
    existing = Cart.query.filter_by(user_id=current_user.id, book_id=book_id).first()
    if not existing:
        cart_item = Cart(user_id=current_user.id, book_id=book_id)
        db.session.add(cart_item)
        db.session.commit()
        flash('Книгу додано до кошика!', 'success')
    else:
        flash('Книга вже у вашому кошику', 'info')
    return redirect(request.referrer or url_for('books'))

@app.route('/cart/remove/<int:book_id>')
@login_required
def remove_from_cart(book_id):
    item = Cart.query.filter_by(user_id=current_user.id, book_id=book_id).first()
    if item:
        db.session.delete(item)
        db.session.commit()
        flash('Книгу видалено з кошика', 'success')
    return redirect(url_for('profile'))

@app.route('/cart/checkout')
@login_required
def checkout_cart():
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    
    if not cart_items:
        flash('Ваш кошик порожній', 'warning')
        return redirect(url_for('profile'))
    
    # Бронюємо всі книги з кошика
    librarian = User.query.filter_by(role='librarian').first()
    if not librarian:
        librarian = User.query.filter_by(role='admin').first()
    
    for item in cart_items:
        book = Book.query.get(item.book_id)
        if book.available_copies > 0:
            loan = Loan(
                book_id=book.id,
                reader_id=current_user.id,
                librarian_id=librarian.id if librarian else current_user.id,
                loan_date=datetime.now().date(),
                due_date=datetime.now().date() + timedelta(days=14),
                status='active'
            )
            book.available_copies -= 1
            db.session.add(loan)
            db.session.delete(item)
    
    db.session.commit()
    flash('Всі книги з кошика успішно заброньовано!', 'success')
    return redirect(url_for('profile'))

# ========== ВІДСТЕЖЕННЯ ==========

@app.route('/tracking/add/<int:book_id>')
@login_required
def add_to_tracking(book_id):
    existing = Tracking.query.filter_by(user_id=current_user.id, book_id=book_id).first()
    if not existing:
        tracking_item = Tracking(user_id=current_user.id, book_id=book_id)
        db.session.add(tracking_item)
        db.session.commit()
        flash('Ви підписалися на сповіщення про появу книги', 'success')
    else:
        flash('Ви вже відстежуєте цю книгу', 'info')
    return redirect(request.referrer or url_for('books'))

@app.route('/tracking/remove/<int:book_id>')
@login_required
def remove_from_tracking(book_id):
    item = Tracking.query.filter_by(user_id=current_user.id, book_id=book_id).first()
    if item:
        db.session.delete(item)
        db.session.commit()
        flash('Відстеження книги скасовано', 'success')
    return redirect(url_for('profile'))

# ========== ПРОДОВЖЕННЯ БРОНЮВАННЯ ==========

@app.route('/loan/extend/<int:loan_id>')
@login_required
def extend_loan(loan_id):
    loan = Loan.query.get_or_404(loan_id)
    
    # Перевіряємо, що це книга користувача
    if loan.reader_id != current_user.id:
        flash('Це не ваша книга!', 'danger')
        return redirect(url_for('profile'))
    
    # Перевіряємо, чи можна продовжити
    if loan.status != 'active':
        flash('Книга вже повернута', 'warning')
        return redirect(url_for('profile'))
    
    # Перевіряємо, чи вже продовжували
    history = UserLoanHistory.query.filter_by(loan_id=loan.id).first()
    if history and history.extended:
        flash('Ви вже продовжували цю книгу. Продовження можливе лише один раз.', 'warning')
        return redirect(url_for('profile'))
    
    # Продовжуємо на 14 днів
    new_due_date = loan.due_date + timedelta(days=14)
    loan.due_date = new_due_date
    
    # Зберігаємо історію продовження
    user_history = UserLoanHistory(
        user_id=current_user.id,
        loan_id=loan.id,
        extended=True,
        extended_until=new_due_date
    )
    db.session.add(user_history)
    db.session.commit()
    
    flash(f'Бронювання продовжено до {new_due_date.strftime("%d.%m.%Y")}!', 'success')
    return redirect(url_for('profile'))

# Створення бази даних при запуску (для Railway)
with app.app_context():
    db.create_all()
    
    # Додаємо тестові дані, якщо їх немає
    if User.query.count() == 0:
        # Користувачі
        admin = User(username='admin', password=generate_password_hash('admin123'), role='admin', full_name='Адміністратор')
        librarian = User(username='librarian', password=generate_password_hash('lib123'), role='librarian', full_name='Марія Петрівна')
        reader_user = User(username='reader', password=generate_password_hash('reader123'), role='reader', full_name='Іван Коваленко')
        db.session.add_all([admin, librarian, reader_user])
        db.session.commit()
        
        # Книги з жанрами
        books = [
            Book(title='Кобзар', author='Тарас Шевченко', year=1840, publisher='Дніпро', genre='Поезія', total_copies=5, available_copies=5),
            Book(title='Кайдашева сім\'я', author='Іван Нечуй-Левицький', year=1878, publisher='Наукова думка', genre='Класика', total_copies=3, available_copies=3),
            Book(title='Тіні забутих предків', author='Михайло Коцюбинський', year=1911, publisher='Либідь', genre='Класика', total_copies=2, available_copies=2),
            Book(title='Зачарована Десна', author='Олександр Довженко', year=1956, publisher='Дніпро', genre='Проза', total_copies=4, available_copies=4),
            Book(title='Собор', author='Олесь Гончар', year=1968, publisher='Український письменник', genre='Роман', total_copies=3, available_copies=3),
            Book(title='Лісова пісня', author='Леся Українка', year=1911, publisher='Веселка', genre='Драма', total_copies=6, available_copies=6),
            Book(title='Маруся', author='Григорій Квітка-Основ\'яненко', year=1834, publisher='Фоліо', genre='Класика', total_copies=2, available_copies=2),
            Book(title='Тигролови', author='Іван Багряний', year=1944, publisher='Смолоскип', genre='Пригоди', total_copies=4, available_copies=4),
            Book(title='Мина Мазайло', author='Микола Куліш', year=1929, publisher='Либідь', genre='Комедія', total_copies=2, available_copies=2),
            Book(title='Сто сонць', author='Любко Дереш', year=2018, publisher='Клуб сімейного дозвілля', genre='Сучасна література', total_copies=3, available_copies=3),
        ]
        db.session.add_all(books)
        db.session.commit()
        
        # Читачі
        readers = [
            Reader(card_number='001', full_name='Олена Шевченко', phone='0981112233', email='olena@example.com', address='вул. Шевченка, 10', user_id=reader_user.id),
            Reader(card_number='002', full_name='Петро Мельник', phone='0972223344', email='petro@example.com', address='пр. Свободи, 5', user_id=None),
            Reader(card_number='003', full_name='Наталія Коваль', phone='0963334455', email='natalia@example.com', address='вул. Франка, 15', user_id=None),
        ]
        db.session.add_all(readers)
        db.session.commit()
        
        # Інформація про бібліотеку
        if LibraryInfo.query.count() == 0:
            info = LibraryInfo(
                working_hours="Понеділок - П'ятниця: 9:00 - 20:00\nСубота: 10:00 - 18:00\nНеділя: Вихідний",
                contacts="вул. Книжкова, 15, Львів\n+380 (32) 123-45-67\nlibrary@example.com",
                history="Наша бібліотека заснована у 1950 році.",
                address="м. Львів, вул. Книжкова, 15"
            )
            db.session.add(info)
            db.session.commit()
        
        print("Базу даних створено з тестовими даними!")

if __name__ == '__main__':
    app.run(debug=True)

    # ========== ОСОБИСТИЙ КАБІНЕТ ==========

