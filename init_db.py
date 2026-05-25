from app import app, db, User, Book, Reader, Loan
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta

def init_db():
    with app.app_context():
        # Видаляємо старі таблиці та створюємо нові
        db.drop_all()
        db.create_all()
        
        # Створюємо користувачів
        admin = User(
            username='admin',
            password=generate_password_hash('admin123'),
            role='admin',
            full_name='Адміністратор Системи'
        )
        
        librarian = User(
            username='librarian',
            password=generate_password_hash('lib123'),
            role='librarian',
            full_name='Марія Петрівна'
        )
        
        reader_user = User(
            username='reader',
            password=generate_password_hash('reader123'),
            role='reader',
            full_name='Іван Коваленко'
        )
        
        db.session.add_all([admin, librarian, reader_user])
        db.session.commit()
        
        # Додаємо книги
        books = [
            Book(title='Кобзар', author='Тарас Шевченко', year=1840, publisher='Дніпро', total_copies=5, available_copies=5),
            Book(title='Кайдашева сім\'я', author='Іван Нечуй-Левицький', year=1878, publisher='Наукова думка', total_copies=3, available_copies=3),
            Book(title='Тіні забутих предків', author='Михайло Коцюбинський', year=1911, publisher='Либідь', total_copies=2, available_copies=2),
            Book(title='Зачарована Десна', author='Олександр Довженко', year=1956, publisher='Дніпро', total_copies=4, available_copies=4),
            Book(title='Собор', author='Олесь Гончар', year=1968, publisher='Український письменник', total_copies=3, available_copies=3),
            Book(title='Лісова пісня', author='Леся Українка', year=1911, publisher='Веселка', total_copies=6, available_copies=6),
            Book(title='Маруся', author='Григорій Квітка-Основ\'яненко', year=1834, publisher='Фоліо', total_copies=2, available_copies=2),
            Book(title='Хіба ревуть воли, як ясла повні?', author='Панас Мирний', year=1880, publisher='Дніпро', total_copies=3, available_copies=3),
            Book(title='Тигролови', author='Іван Багряний', year=1944, publisher='Смолоскип', total_copies=4, available_copies=4),
            Book(title='Мина Мазайло', author='Микола Куліш', year=1929, publisher='Либідь', total_copies=2, available_copies=2),
        ]
        
        db.session.add_all(books)
        db.session.commit()
        
        # Додаємо читачів
        readers = [
            Reader(card_number='001', full_name='Олена Шевченко', phone='0981112233', email='olena@example.com', address='вул. Шевченка, 10'),
            Reader(card_number='002', full_name='Петро Мельник', phone='0972223344', email='petro@example.com', address='пр. Свободи, 5'),
            Reader(card_number='003', full_name='Наталія Коваль', phone='0963334455', email='natalia@example.com', address='вул. Франка, 15'),
        ]
        
        db.session.add_all(readers)
        db.session.commit()
        
        # Додаємо декілька видач (для демонстрації)
        reader1 = Reader.query.get(1)
        reader2 = Reader.query.get(2)
        book1 = Book.query.get(1)
        book2 = Book.query.get(3)
        librarian_user = User.query.filter_by(role='librarian').first()
        
        loans = [
            Loan(book_id=1, reader_id=1, librarian_id=2, loan_date=datetime.now().date() - timedelta(days=5), 
                 due_date=datetime.now().date() + timedelta(days=9), status='active'),
            Loan(book_id=3, reader_id=2, librarian_id=2, loan_date=datetime.now().date() - timedelta(days=20), 
                 due_date=datetime.now().date() - timedelta(days=6), status='active'),
            Loan(book_id=5, reader_id=1, librarian_id=2, loan_date=datetime.now().date() - timedelta(days=30), 
                 due_date=datetime.now().date() - timedelta(days=16), return_date=datetime.now().date() - timedelta(days=15), status='returned'),
        ]
        
        # Зменшуємо доступну кількість книг для активних видач
        for book in Book.query.all():
            book.available_copies = book.total_copies
        
        book1 = Book.query.get(1)
        book3 = Book.query.get(3)
        book1.available_copies -= 1
        book3.available_copies -= 1
        
        db.session.add_all(loans)
        db.session.commit()
        
        print("Базу даних створено успішно!")
        print("\nЛогіни та паролі для входу:")
        print("  Адміністратор: admin / admin123")
        print("  Бібліотекар: librarian / lib123")
        print("  Читач: reader / reader123")

if __name__ == '__main__':
    init_db()